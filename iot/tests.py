from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID

import paho.mqtt.client as mqtt
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

from iot import mqtt_client
from iot.device_heartbeat_worker import parse_device_heartbeat, process_device_heartbeat
from iot.helpers import transform_telemetry_payload
from iot.models.device_models import Device
from iot.streaming import DEVICE_HEARTBEAT_TOPIC
from iot.utils import device_pairing_cache
from iot.views import iot_device_views

DEVICE_ID = "0123456789abcdef0123456789abcdef"


class DeviceHeartbeatQueueTests(SimpleTestCase):
    def setUp(self):
        self.original_listeners = mqtt_client._topic_listeners
        mqtt_client._topic_listeners = {}
        self.subscribe_patcher = patch.object(mqtt_client._mqtt_client, "subscribe")
        self.subscribe_patcher.start()
        self.addCleanup(self.subscribe_patcher.stop)

    def tearDown(self):
        mqtt_client._topic_listeners = self.original_listeners

    def test_topic_matches_all_device_heartbeats(self):
        self.assertTrue(
            mqtt.topic_matches_sub(
                DEVICE_HEARTBEAT_TOPIC, "device/device/device1/heartbeat"
            )
        )
        self.assertTrue(
            mqtt.topic_matches_sub(
                DEVICE_HEARTBEAT_TOPIC, f"device/sensor/{DEVICE_ID}/heartbeat"
            )
        )
        self.assertFalse(
            mqtt.topic_matches_sub(DEVICE_HEARTBEAT_TOPIC, "devices/device1/heartbeat")
        )

    def test_heartbeat_queue_receives_topic_and_payload(self):
        heartbeat_queue = mqtt_client.subscribe_and_listen(
            DEVICE_HEARTBEAT_TOPIC, include_topic=True
        )
        message = SimpleNamespace(
            topic="device/device/device1/heartbeat",
            payload=b'{"status":"alive"}',
        )

        mqtt_client.on_message(None, None, message)

        self.assertEqual(
            heartbeat_queue.get_nowait(),
            ("device/device/device1/heartbeat", '{"status":"alive"}'),
        )

    def test_existing_queues_still_receive_payload_only(self):
        sensor_queue = mqtt_client.subscribe_and_listen("sensor/+/heartbeat")
        heartbeat_queue = mqtt_client.subscribe_and_listen(
            DEVICE_HEARTBEAT_TOPIC, include_topic=True
        )
        message = SimpleNamespace(topic="sensor/sensor1/heartbeat", payload=b"alive")

        mqtt_client.on_message(None, None, message)

        self.assertEqual(sensor_queue.get_nowait(), "alive")
        self.assertTrue(heartbeat_queue.empty())

    def test_parse_device_heartbeat(self):
        self.assertEqual(
            parse_device_heartbeat(
                (f"device/temperature/{DEVICE_ID}/heartbeat", '{"status":"alive"}')
            ),
            ("temperature", DEVICE_ID, {"status": "alive"}),
        )


class DeviceHeartbeatPairingTests(SimpleTestCase):
    def test_worker_ignores_unverified_device(self):
        message = (f"device/device/{DEVICE_ID}/heartbeat", '{"status":"alive"}')

        with (
            patch(
                "iot.device_heartbeat_worker.is_device_paired_and_verified",
                return_value=False,
            ) as is_paired,
            patch("iot.device_heartbeat_worker.complete_device_pairing") as complete,
        ):
            result = process_device_heartbeat(message)

        self.assertFalse(result)
        is_paired.assert_called_once_with(DEVICE_ID)
        complete.assert_not_called()

    def test_worker_accepts_paired_device(self):
        message = (f"device/device/{DEVICE_ID}/heartbeat", '{"status":"alive"}')

        with (
            patch(
                "iot.device_heartbeat_worker.is_device_paired_and_verified",
                return_value=True,
            ) as is_paired,
            patch("iot.device_heartbeat_worker.complete_device_pairing") as complete,
        ):
            result = process_device_heartbeat(message)

        self.assertTrue(result)
        is_paired.assert_called_once_with(DEVICE_ID)
        complete.assert_called_once_with(DEVICE_ID)


class DevicePairingCacheTests(SimpleTestCase):
    def test_mark_and_check_pairing_state(self):
        redis_client = Mock()
        redis_client.hget.return_value = device_pairing_cache.PAIRING

        with patch.object(
            device_pairing_cache, "_get_redis_client", return_value=redis_client
        ):
            device_pairing_cache.mark_device_pairing(DEVICE_ID)
            is_paired = device_pairing_cache.is_device_paired_and_verified(DEVICE_ID)

        redis_client.hset.assert_called_once_with(
            device_pairing_cache.DEVICE_PAIRING_HASH,
            DEVICE_ID,
            device_pairing_cache.PAIRING,
        )
        redis_client.hget.assert_called_once_with(
            device_pairing_cache.DEVICE_PAIRING_HASH, DEVICE_ID
        )
        self.assertTrue(is_paired)

    def test_mark_unpaired_disables_pairing_check(self):
        redis_client = Mock()
        redis_client.hget.return_value = device_pairing_cache.UNPAIRED

        with patch.object(
            device_pairing_cache, "_get_redis_client", return_value=redis_client
        ):
            device_pairing_cache.mark_device_unpaired(DEVICE_ID)
            is_paired = device_pairing_cache.is_device_paired_and_verified(DEVICE_ID)

        redis_client.hset.assert_called_once_with(
            device_pairing_cache.DEVICE_PAIRING_HASH,
            DEVICE_ID,
            device_pairing_cache.UNPAIRED,
        )
        self.assertFalse(is_paired)


class PairDeviceViewTests(SimpleTestCase):
    def test_pair_device_marks_device_as_pairing(self):
        device = SimpleNamespace(
            id=DEVICE_ID,
            name="Test Device",
            is_paired=Device.PairingChoice.UNPAIRED,
            save=Mock(),
        )
        request = RequestFactory().post("/")
        request.user = SimpleNamespace(organization=object(), is_authenticated=True)
        view = iot_device_views.paired_device_and_fetched_sesnors.__wrapped__

        with (
            patch.object(
                iot_device_views, "get_object_or_404", return_value=device
            ) as get_device,
            patch.object(iot_device_views, "mark_device_pairing") as mark_pairing,
            patch.object(iot_device_views.messages, "success"),
            patch.object(
                iot_device_views, "redirect", return_value="redirected"
            ) as redirect_mock,
        ):
            response = view(request, DEVICE_ID)

        self.assertEqual(response, "redirected")
        self.assertEqual(device.is_paired, Device.PairingChoice.PAIRING)
        device.save.assert_called_once_with(update_fields=["is_paired"])
        mark_pairing.assert_called_once_with(DEVICE_ID)
        get_device.assert_called_once()
        redirect_mock.assert_called_once_with("iot:devices_list")

    def test_pair_device_rejects_get(self):
        request = RequestFactory().get("/")
        request.user = SimpleNamespace(organization=object(), is_authenticated=True)
        view = iot_device_views.paired_device_and_fetched_sesnors.__wrapped__

        response = view(request, DEVICE_ID)

        self.assertEqual(response.status_code, 405)

    def test_unpair_device_marks_device_as_unpaired(self):
        device = SimpleNamespace(
            id=DEVICE_ID,
            name="Test Device",
            is_paired=Device.PairingChoice.PAIRED,
            save=Mock(),
        )
        request = RequestFactory().post("/")
        request.user = SimpleNamespace(organization=object(), is_authenticated=True)
        view = iot_device_views.unpair_device.__wrapped__

        with (
            patch.object(
                iot_device_views, "get_object_or_404", return_value=device
            ) as get_device,
            patch.object(iot_device_views, "mark_device_unpaired") as mark_unpaired,
            patch.object(iot_device_views.messages, "success"),
            patch.object(
                iot_device_views, "redirect", return_value="redirected"
            ) as redirect_mock,
        ):
            response = view(request, DEVICE_ID)

        self.assertEqual(response, "redirected")
        self.assertEqual(device.is_paired, Device.PairingChoice.UNPAIRED)
        device.save.assert_called_once_with(update_fields=["is_paired"])
        mark_unpaired.assert_called_once_with(DEVICE_ID)
        get_device.assert_called_once()
        redirect_mock.assert_called_once_with("iot:devices_list")


class PairingStatusViewTests(SimpleTestCase):
    def test_pairing_status_renders_current_state(self):
        device = SimpleNamespace(id=UUID(DEVICE_ID), is_paired=1)
        request = RequestFactory().get("/")
        request.user = SimpleNamespace(organization=object(), is_authenticated=True)
        view = iot_device_views.device_pairing_status.__wrapped__

        with (
            patch.object(
                iot_device_views, "get_object_or_404", return_value=device
            ) as get_device,
            patch.object(
                iot_device_views, "render", return_value="status"
            ) as render_mock,
        ):
            response = view(request, DEVICE_ID)

        self.assertEqual(response, "status")
        get_device.assert_called_once()
        render_mock.assert_called_once_with(
            request,
            "iot_devices/device-pairing-status.html",
            {"device_id": DEVICE_ID, "is_paired": 1},
        )


class PairingStatusTemplateTests(SimpleTestCase):
    def test_pairing_badge_exposes_poll_target_while_pairing(self):
        html = render_to_string(
            "iot_devices/device-pairing-status.html",
            {"device_id": DEVICE_ID, "is_paired": 1},
        )

        self.assertIn('data-pairing-active="true"', html)
        self.assertIn(f"/iot/devices/{DEVICE_ID}/pairing-status", html)
        self.assertIn("spinner-border", html)


class TelemetryPayloadTransformTests(SimpleTestCase):
    def test_flat_payload_uses_raw_keys_without_unit(self):
        payload = {
            "device_id": "machine_001",
            "timestamp": 1795591800000,
            "temperature": 29.5,
            "humidity": 65,
            "sound_level": 42,
            "pressure": 1013.25,
        }

        self.assertEqual(
            transform_telemetry_payload(payload),
            {
                "sensors": [
                    {"id": "machine_001", "type": "temperature", "value": 29.5},
                    {"id": "machine_001", "type": "humidity", "value": 65},
                    {"id": "machine_001", "type": "sound_level", "value": 42},
                    {"id": "machine_001", "type": "pressure", "value": 1013.25},
                ]
            },
        )

    def test_device_keyed_dynamic_values_become_sensors(self):
        payload = {
            DEVICE_ID: {"temperature": 28, "sound_level": 51},
            "DEV-456": {"vibration": 1.2},
        }

        self.assertEqual(
            transform_telemetry_payload(payload)["sensors"],
            [
                {"id": DEVICE_ID, "type": "temperature", "value": 28},
                {"id": DEVICE_ID, "type": "sound_level", "value": 51},
                {"id": "DEV-456", "type": "vibration", "value": 1.2},
            ],
        )

    def test_legacy_sensors_payload_is_still_supported(self):
        payload = {
            "sensors": [
                {"device_id": DEVICE_ID, "type": "temperature", "temperature": 26}
            ]
        }

        self.assertEqual(
            transform_telemetry_payload(payload)["sensors"],
            [{"id": DEVICE_ID, "type": "temperature", "value": 26}],
        )
