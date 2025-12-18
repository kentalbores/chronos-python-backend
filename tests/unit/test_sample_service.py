import pytest

from src.services.sample import SampleService


@pytest.mark.asyncio
async def test_add():
    service = SampleService()

    expected_sum = 5
    result = await service.add(num1=3, num2=2)
    assert result == expected_sum
