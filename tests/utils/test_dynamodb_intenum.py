from enum import IntEnum

import pytest
from django.conf import settings
from moto import mock_dynamodb2
from pynamodb.attributes import NumberAttribute
from pynamodb.models import Model

from hsreplaynet.utils.dynamodb import IntEnumAttribute


class CustomEnum(IntEnum):
	HEADS = 1
	TAILS = 2


class IntEnumTest(Model):
	id = NumberAttribute(hash_key=True)
	enum_field = IntEnumAttribute(CustomEnum)
	null_field = IntEnumAttribute(CustomEnum, null=True)

	class Meta:
		table_name = settings.DYNAMODB_TABLES["intenum_test"]["NAME"]
		host = settings.DYNAMODB_TABLES["intenum_test"]["HOST"]
		read_capacity_units = 2
		write_capacity_units = 5


@pytest.fixture
def intenum_test_dynamodb_table():
	with (mock_dynamodb2()):
		meta_values = {
			k: IntEnumTest.Meta.__dict__[k]
			for k in ["host", "aws_access_key_id", "aws_secret_access_key"]
		}

		IntEnumTest.Meta.host = None
		IntEnumTest.Meta.aws_access_key_id = "test"
		IntEnumTest.Meta.aws_secret_access_key = "test"

		IntEnumTest.create_table(wait=True)
		yield
		IntEnumTest.delete_table()

		for k, v in meta_values.items():
			setattr(IntEnumTest.Meta, k, v)


@pytest.mark.usefixtures("intenum_test_dynamodb_table")
def test_dynamodb_int_enum_attribute():
	obj = IntEnumTest(id=1, enum_field=CustomEnum.TAILS, null_field=None)
	obj.save()
	assert obj.enum_field == 2
	assert obj.enum_field == CustomEnum.TAILS
	assert isinstance(obj.enum_field, CustomEnum)
	assert obj.null_field is None

	res = IntEnumTest.get(1)
	assert res.enum_field == 2
	assert res.enum_field == CustomEnum.TAILS
	assert isinstance(res.enum_field, CustomEnum)
	assert res.null_field is None
