import inspect
from telegram.ext import Application

print(inspect.signature(Application.run_polling))
print('-' * 40)
print(inspect.iscoroutinefunction(Application.run_polling))
