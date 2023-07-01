class CustomUserForeignKeyInput(graphene.InputObjectType):
    alias = graphene.String(required=True)

input_type_cache = {}

def get_input_type_for_model(model):
    if model in input_type_cache:
        return input_type_cache[model]
    
    fields = {}
    for field in model._meta.get_fields():
        if isinstance(field, models.CharField) or isinstance(field, models.TextField) or isinstance(field, models.EmailField):
            fields[field.name] = graphene.String(required=not field.blank)
        elif isinstance(field, models.IntegerField):
            fields[field.name] = graphene.Int(required=not field.blank)
        elif isinstance(field, models.BooleanField):
            fields[field.name] = graphene.Boolean(required=not field.blank)
        elif isinstance(field, models.FloatField):
            fields[field.name] = graphene.Float(required=not field.blank)
        elif isinstance(field, models.DecimalField):
            fields[field.name] = graphene.Decimal(required=not field.blank)
        elif isinstance(field, models.DateField):
            fields[field.name] = graphene.Date(required=not field.blank)
        elif isinstance(field, models.DateTimeField):
            fields[field.name] = graphene.DateTime(required=not field.blank)
        if isinstance(field, models.ForeignKey):
            if field.related_model != apps.get_model('users', 'CustomUser'):  # Exclude User model
                related_model_input_type = get_input_type_for_model(field.related_model)
                fields[field.name] = graphene.Field(related_model_input_type, required=not field.blank)
            else:
                fields[field.name] = graphene.Field(CustomUserForeignKeyInput, required=not field.blank)
        if isinstance(field, models.ManyToManyField):
            if field.related_model != apps.get_model('users', 'CustomUser').__name__:  # Exclude User model
                # To allow creating new related instances, generate an InputObjectType for the related model:
                related_model_input_type = get_input_type_for_model(field.related_model)
                fields[field.name] = graphene.List(graphene.NonNull(related_model_input_type), required=not field.blank)
            else:
                related_model_input_type = get_input_type_for_model(field.related_model)
                fields[field.name] = graphene.List(graphene.NonNull(related_model_input_type), required=not field.blank)

    Meta = type('Meta', (object,), {'model': model})
    input_type = type(model.__name__ + 'InputType', (graphene.InputObjectType,), fields)
    input_type.Meta = Meta

    input_type_cache[model] = input_type

    return input_type


def create_mutations_for_app(
    app_name, 
    model_names, 
    mutation_name_format, 
    output_message_format, 
    related_model_map=None, 
    validation_func_map=None,
    model=None
):
    app = apps.get_app_config(app_name)
    mutations = []
    mutation_map = {}

    for model in app.get_models():
        if model.__name__ in model_names:
            ModelInputType = get_input_type_for_model(model)

            class UpdateOrCreateModelMutation(graphene.Mutation):
                class Arguments:
                    input = ModelInputType(required=True)

                Output = SuccessMutationResult

                @classmethod
                def mutate(cls, root, info, input):
                    if validation_func_map and model.__name__ in validation_func_map:
                        validation_func = validation_func_map[model.__name__]
                        errors = validation_func(input)
                        if errors:
                            return FailureMessage(success=False, message=f"There are validation errors", errors=errors)
                    try:
                        with transaction.atomic():
                            model_instance = update_or_create_object(model, input, related_model_map=related_model_map)
                            if model_instance:
                                output_message = output_message_format.format(model=model.__name__, id=model_instance.id)
                                return SuccessMessage(success=True, id=str(model_instance.id), message=output_message)
                    except Exception as e:
                        return FailureMessage(success=False, message=f"Error creating or updating {model.__name__}", errors=[str(e)])

            mutation_name = mutation_name_format.format(model=model.__name__)
            UpdateOrCreateModelMutation.__name__ = mutation_name
            mutations.append(UpdateOrCreateModelMutation)
            mutation_map[mutation_name] = UpdateOrCreateModelMutation

    return mutations, mutation_map


def create_delete_mutation_for_app(app_name, model_names):
    app = apps.get_app_config(app_name)
    mutations = []
    mutation_map = {}

    for model in app.get_models():
        if model.__name__ in model_names:
            class DeleteMutation(graphene.Mutation):
                class Arguments:
                    id = graphene.ID(required=True)

                Output = SuccessMutationResult

                @classmethod
                def mutate(cls, root, info, id):
                    try:
                        with transaction.atomic():
                            model_instance = model.objects.get(id=id)
                            model_instance.delete()
                            return SuccessMessage(success=True, id=str(id), message="Object deleted successfully")
                    except Exception as e:
                        return FailureMessage(success=False, message=f"Error deleting object", errors=[str(e)])

            mutation_name = f"{model.__name__}Delete"
            DeleteMutation.__name__ = mutation_name
            # setattr(sys.modules[__name__], mutation_name, DeleteMutation)
            # mutations.append(DeleteMutation)

            mutations.append(DeleteMutation)
            mutation_map[mutation_name] = DeleteMutation
    return mutations, mutation_map
