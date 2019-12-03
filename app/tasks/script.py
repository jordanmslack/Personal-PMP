from app.tasks.methods import *
from decouple import config

board_id = '5a85af5db6f9f29b4a97b8d1'
member_id = '500f35c448c6812f07398e5f'
trello = Trello(api_key=config('TRELLO_API_KEY'), api_token=config('TRELLO_API_TOKEN'))
response = trello.add_board_member(board_id=board_id, member_id=member_id)
