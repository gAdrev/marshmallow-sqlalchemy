# -*- coding: utf-8 -*-
import marshmallow as ma
from marshmallow.compat import with_metaclass

from .convert import ModelConverter


class TableSchemaOpts(ma.SchemaOpts):
    """Options class for `TableSchema`.
    Adds the following options:

    - ``table``: The SQLAlchemy table to generate the `Schema` from (required).
    - ``model_converter``: `ModelConverter` class to use for converting the SQLAlchemy table to
        marshmallow fields.
    - ``include_fk``: Whether to include foreign fields; defaults to `False`.
    """

    def __init__(self, meta, *args, **kwargs):
        super(TableSchemaOpts, self).__init__(meta, *args, **kwargs)
        self.table = getattr(meta, 'table', None)
        self.model_converter = getattr(meta, 'model_converter', ModelConverter)
        self.include_fk = getattr(meta, 'include_fk', False)

class ModelSchemaOpts(ma.SchemaOpts):
    """Options class for `ModelSchema`.
    Adds the following options:

    - ``model``: The SQLAlchemy model to generate the `Schema` from (required).
    - ``model_converter``: `ModelConverter` class to use for converting the SQLAlchemy model to
        marshmallow fields.
    - ``include_fk``: Whether to include foreign fields; defaults to `False`.
    """

    def __init__(self, meta, *args, **kwargs):
        super(ModelSchemaOpts, self).__init__(meta, *args, **kwargs)
        self.model = getattr(meta, 'model', None)
        self.model_converter = getattr(meta, 'model_converter', ModelConverter)
        self.include_fk = getattr(meta, 'include_fk', False)

class SchemaMeta(ma.schema.SchemaMeta):
    """Metaclass for `ModelSchema`."""

    # override SchemaMeta
    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        """Updates declared fields with fields converted from the SQLAlchemy model
        passed as the `model` class Meta option.
        """
        declared_fields = dict_cls()
        opts = klass.opts
        Converter = opts.model_converter
        converter = Converter(schema_cls=klass)
        base_fields = super(SchemaMeta, mcs).get_declared_fields(
            klass, cls_fields, inherited_fields, dict_cls
        )
        declared_fields = mcs.get_fields(converter, opts, base_fields, dict_cls)
        declared_fields.update(base_fields)
        return declared_fields

    @classmethod
    def get_fields(mcs, converter, base_fields, opts):
        pass

class TableSchemaMeta(SchemaMeta):

    @classmethod
    def get_fields(mcs, converter, opts, base_fields, dict_cls):
        if opts.table is not None:
            return converter.fields_for_table(
                opts.table,
                fields=opts.fields,
                exclude=opts.exclude,
                include_fk=opts.include_fk,
                base_fields=base_fields,
                dict_cls=dict_cls,
            )
        return dict_cls()

class ModelSchemaMeta(SchemaMeta):

    @classmethod
    def get_fields(mcs, converter, opts, base_fields, dict_cls):
        if opts.model is not None:
            return converter.fields_for_model(
                opts.model,
                fields=opts.fields,
                exclude=opts.exclude,
                include_fk=opts.include_fk,
                base_fields=base_fields,
                dict_cls=dict_cls,
            )
        return dict_cls()

class TableSchema(with_metaclass(TableSchemaMeta, ma.Schema)):
    """Base class for SQLAlchemy model-based Schemas.

    Example: ::

        from marshmallow_sqlalchemy import TableSchema
        from mymodels import engine, users

        class UserSchema(TableSchema):
            class Meta:
                table = users

        schema = UserSchema()

        select = users.select().limit(1)
        user = engine.execute(select).fetchone()
        serialized = schema.dump(user).data
    """
    OPTIONS_CLASS = TableSchemaOpts

class ModelSchema(with_metaclass(ModelSchemaMeta, ma.Schema)):
    """Base class for SQLAlchemy model-based Schemas.

    Example: ::

        from marshmallow_sqlalchemy import ModelSchema
        from mymodels import User, session

        class UserSchema(ModelSchema):
            class Meta:
                model = User

        schema = UserSchema()

        user = schema.load({'name': 'Bill'}, session=session)
        existing_user = schema.load({'name': 'Bill'}, instance=User.query.first())

    :param session: Optional SQLAlchemy session; may be overridden in `load.`
    :param instance: Optional existing instance to modify; may be overridden in `load`.
    """
    OPTIONS_CLASS = ModelSchemaOpts

    def __init__(self, *args, **kwargs):
        super(ModelSchema, self).__init__(*args, **kwargs)

    def load(self, data, *args, **kwargs):
        """Deserialize data to internal representation.
        """
        ret = super(ModelSchema, self).load(data, *args, **kwargs)
        return ret

    def validate(self, data, *args, **kwargs):
        return super(ModelSchema, self).validate(data, *args, **kwargs)
