from gslides_api import Presentation, initialize_credentials

credential_location = ""

initialize_credentials(credential_location)

# Создаем пустую презентацию
new_presentation = Presentation.create_blank("Тестовая презентация")

print("Создана новая презентация:")
print(new_presentation.url)
