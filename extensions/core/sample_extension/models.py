from django.db import models


class SamplePing(models.Model):
    """Trivial model proving the extension's own migrations apply cleanly."""

    message = models.CharField(max_length=100, default="pong")
