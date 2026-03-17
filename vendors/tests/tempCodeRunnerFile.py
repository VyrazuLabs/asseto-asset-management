def login(self):
        driver = webdriver.Chrome()
        driver.maximize_window()

        driver.execute_cdp_cmd("Network.enable", {})

        auth = {'username': 'admin', 'password': 'admin'}

        credentials = f"{auth['username']}:{auth['password']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # driver.execute_cdp_cmd(
        #     "Network.setExtraHTTPHeaders",
        #     {"headers": {"Authorization": f"Basic {encoded_credentials}"}}
        # )
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders',{
            'headers':{
                'Authorization': 'Basic' + base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
                }
            }
        )
        # driver.get("http://10.0.0.117:9000/login")
        vendors_url = "http://10.0.0.117:9000/vendors/list"
        print("logged in")
        self.driver.get(vendors_url)
        time.sleep(5)
        driver.quit()