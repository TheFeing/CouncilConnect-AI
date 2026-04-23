import locust   # Load testing framework for simulating user behavior

class CouncilUser(locust.HttpUser): # CouncilUser class inherits from HttpUser to simulate HTTP requests.
    wait_time = locust.between(1, 2) # wait_time is set to 1 to 2 seconds delay between tasks to mimic real user behavior.

    @locust.task(5) # Wrap the next function as a locust task with a weight of 5.
    def ask_council_tax(self):  # 'self' ensures each simulated request is independent and can maintain its own state if needed. 
        self.client.post("/chat", json={"prompt": "How do I apply for a council tax reduction?"})

    @locust.task(1)
    def check_health(self):
        self.client.get("/health")