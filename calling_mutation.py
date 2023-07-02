class Mutation(graphene.ObjectType):
    feedback_update_or_create = FeedbackUpdateOrCreate.Field()
    feedback_delete = FeedbackDelete.Field()


# Validation functions
def validate_model1_input(input):
    validation_errors = []

    # Perform validations specific to Model1 input
    if input.get('field1') is None:
        validation_errors.append('Field1 is required.')

    # Add more validations...

    return validation_errors

def validate_model2_input(input):
    validation_errors = []

    # Perform validations specific to Model2 input
    if input.get('field2') is None:
        validation_errors.append('Field2 is required.')
        
    return validation_errors

def no_validation(input):
    return []
        

validation_func_map = {
    'FeedBack': no_validation,
    'FeedBackActions': no_validation,
    'Notices': no_validation,
    'NoticeRead': no_validation
}


# Generate mutations for specific models in an app
app_name = 'feedback'
model_names = ['FeedBack', 'FeedBackActions', 'Notices', 'NoticeRead']
mutation_name_format = '{model}_update_or_create'
output_message_format = "{model} {action} successfully"
delete_mutation_name_format = '{model}_delete'
delete_output_message_format = "{model} deleted successfully"
validation_functions = validation_func_map
related_model_map = {
    'CustomUser': CustomUser,
}

mutations, mutation_map = create_mutations_for_app(
    app_name, 
    model_names, 
    mutation_name_format, 
    output_message_format, 
    validation_func_map=validation_functions
)

# For delete mutations, also include only models from the list
delete_mutations, delete_mutation_map = create_delete_mutation_for_app(app_name, model_names)

# Add the mutations to the Mutation class
for mutation_name, mutation in mutation_map.items():
    setattr(Mutation, mutation_name, mutation.Field())

for mutation_name, mutation in delete_mutation_map.items():
    setattr(Mutation, mutation_name, mutation.Field())
