import logging


class SampleService:
    def __init__(self):
        self.logger = logging.getLogger("SampleService")

    async def add(
        self,
        num1: float,
        num2: float,
    ) -> float:
        """
        Addition for two numbers

        Args:
            num1 [float]: First number.
            num2 [float]: Second number.

        Returns:
            float: The sum of the two numbers
        """
        log = self.logger.getChild("add")
        log.info(f"Adding two two numbers {num1} {num2}")
        return num1 + num2
