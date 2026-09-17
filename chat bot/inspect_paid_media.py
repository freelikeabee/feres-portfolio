import inspect
from telegram import Bot
print('send_paid_media exists:', hasattr(Bot, 'send_paid_media'))
if hasattr(Bot, 'send_paid_media'):
    print(inspect.signature(Bot.send_paid_media))
print('send_photo sig:', inspect.signature(Bot.send_photo))
print('send_invoice sig:', inspect.signature(Bot.send_invoice))
