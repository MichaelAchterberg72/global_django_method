class UpdateOrCreateMixin:
    from django.db import transaction

    @transaction.atomic
    def update_or_create_object(self, data, related_model_map=None):
        print("############1############")
        obj_id = data.pop('id', None)
        m2m_fields = {}
        foreign_key_fields = {}
        regular_fields = {}
        for field, value in data.items():
            if isinstance(value, list):
                m2m_fields[field] = value
            elif isinstance(value, dict):
                foreign_key_fields[field] = value
            else:
                regular_fields[field] = value
        print("############2############")
        obj = None
        if obj_id:
            obj = self.__class__.objects.filter(id=obj_id).first()
            if obj:
                for field, value in regular_fields.items():
                    setattr(obj, field, value)
                obj.save()
        print("############3############")
        if obj is None:
            if regular_fields:
                print("#######3.1#######")
                create_kwargs = {key: value for key, value in regular_fields.items() if key not in m2m_fields and key not in foreign_key_fields}
                print("#######3.2#######")
                print(create_kwargs)
                try:
                    print("#######3.3#######")
                    print(self.__class__)
                    obj = self.__class__.objects.create(**create_kwargs)
                    print("#######3.4#######")
                except IntegrityError:
                    pass
            else:
                return None
        print("############4############")
        if foreign_key_fields:
            print("############4.1############")
            for field, value in foreign_key_fields.items():
                related_model = getattr(self.__class__, field).field.related_model
                related_obj_id = value.pop('id', None)
                related_obj_slug = value.pop('slug', None)
                print("############4.2############")
                field_obj = self.__class__._meta.get_field(field)
                if related_model_map and related_model.__name__ in related_model_map:
                    related_model = related_model_map[related_model.__name__]
                print("############4.3############")
                if related_model.__name__ == apps.get_model('users', 'CustomUser').__name__:
                    if 'alias' in value:
                        try:
                            print("############4.3.1#############")
                            print(value['alias'])
                            print(related_model)
                            app_label = related_model._meta.app_label
                            model_name = related_model._meta.model_name
                            print(f"App label: {app_label}")
                            print(f"Model name: {model_name}")
                            # Use apps.get_model() to import the model
                            related_model_name = apps.get_model(app_label, model_name)
                            print(f"Model name: {related_model_name}")
                            print(related_model_name.objects.all())
                            print("#####################")
                            related_obj = related_model_name.objects.filter(alias=value['alias']).first()
                            print("############4.3.2#############")
                            setattr(obj, field, related_obj)
                        except Exception as e:
                            print(e)
                            raise
                    continue
                print("############4.4############")
                if not related_model.__name__ == apps.get_model('users', 'CustomUser').__name__:
                    print("############4.4.1############")
                    if related_obj_id:
                        print("############4.4.1.1############")
                        print(related_model)
                        print(related_obj_id)
                        try:
                            app_label = related_model._meta.app_label
                            model_name = related_model._meta.model_name
                            print(app_label)
                            print(model_name)
                            model = apps.get_model(app_label, model_name)
                            print(list(model.objects.all()))
                            related_obj = model.objects.filter(id=related_obj_id).first()
                            print("############4.4.1.1.1############")
                        except Exception as e:
                            print(e)
                            raise
                        if related_obj:
                            setattr(obj, field, related_obj)
                        print("############4.4.2############")
                    elif related_obj_slug:
                        print("############4.4.2.1############")
                        related_obj = related_model.objects.filter(slug=related_obj_slug).first()
                        if related_obj:
                            setattr(obj, field, related_obj)
                        print("############4.4.3############")
                    else:
                        print("############4.4.3.1############")
                        print(obj)
                        if obj is None:
                            continue
                        else:
                            related_obj = obj.update_or_create_object(value, related_model_map=related_model_map)
                            if related_obj is not None:
                                for fk_field in field_obj.foreign_related_fields:
                                    setattr(related_obj, fk_field.name, obj)
                                    setattr(obj, fk_field.name, related_obj)
                                related_obj.save()
                            setattr(obj, field, related_obj)
        print("############5############")
        if m2m_fields:
            for field, value in m2m_fields.items():
                m2m_related_models_data = {
                    'model': getattr(self.__class__, field).field.related_model,
                    'manager': field,
                    'fields': [f.name for f in getattr(self.__class__, field).field.related_model._meta.fields],
                    'data': value,
                }
                
                model = m2m_related_models_data['model']
                manager_name = m2m_related_models_data['manager']
                fields = m2m_related_models_data['fields']
                data_list = m2m_related_models_data['data']

                related_manager = getattr(obj, manager_name)

                for related_data in data_list: 
                    filter_kwargs = {field: related_data.get(field) for field in fields if field != 'id'}
                    related_instance_id = related_data.get('id')
                    
                    if related_instance_id:
                        related_instance = model.objects.filter(id=related_instance_id).first()
                        if related_instance:
                            related_manager.add(related_instance)
                    else:                    
                        related_instance, created = model.objects.get_or_create(**filter_kwargs)
                        related_manager.add(related_instance)
        print("############6############")
        if obj:
            obj.save()
        print("############7############")
        return obj
