import requests
import json
from app.models import *
from decouple import config
from boxsdk import JWTAuth, Client

# TODO https://github.com/robicch/jQueryGantt
# TODO https://github.com/frappe/gantt


def key_path():

    private_key = config('PRIVATE_KEY')

    with open('temp_key.pem', 'w+') as temp_file:
        lines = private_key.split('\n')
        temp_file.writelines([x.replace('\\n', '\n') for x in lines])

    path_name = os.path.join(os.getcwd(), temp_file.name)

    return path_name


def delete_temp_key():

    path_name = key_path()

    if os.path.exists(path_name):
        os.remove(os.path.basename(path_name))


def box_auth():

    path_name = key_path()

    auth = JWTAuth(
        client_id=config('CLIENT_ID'),
        client_secret=config('CLIENT_SECRET'),
        enterprise_id=config('ENTERPRISE_ID'),
        jwt_key_id=config('JWT_KEY_ID'),
        rsa_private_key_file_sys_path=path_name,
        rsa_private_key_passphrase=config('RSA_PRIVATE').encode('utf-8'),
    )
    client = Client(auth)
    user = client.user(user_id=config('BOX_USER_ID'))

    delete_temp_key()

    return client, user


class Trello:

    def __init__(self, api_key, api_token, user=None):
        self.api_key = api_key
        self.api_token = api_token

        if user:
            self.user = user
        else:
            self.user = 'me'

    def get_boards(self):

        params = {'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/boards'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def create_board(self, name, description, default_labels='true', default_lists='false',
                     board_source_id='', keep_source='', power_ups='all', permissions='private',
                     voting_preferences='members', comment_preferences='members', invitation_preferences='members',
                     self_join='false', card_covers='true', background='grey', card_aging='regular'):

        if board_source_id:
            keep_source = 'cards'

        params = {'name': name, 'desc': description, 'defaultLabels': default_labels, 'defaultLists': default_lists,
                  'idBoardSource': board_source_id, 'keepFromSource': keep_source,
                  'powerUps': power_ups, 'prefs_permissionLevel': permissions, 'prefs_voting': voting_preferences,
                  'prefs_comments': comment_preferences, 'prefs_invitations': invitation_preferences,
                  'prefs_selfJoin': self_join, 'prefs_cardCovers': card_covers, 'prefs_background': background,
                  'prefs_cardAging': card_aging, 'key': self.api_key, 'token': self.api_token}

        headers = {'accept': 'application/json'}

        url = 'https://api.trello.com/1/boards/'
        response = requests.post(url, headers=headers, params=params)

        data = json.loads(response.content)

        return data

    def create_group_board(self, group_name, description, type):

        board = self.create_board(name=group_name, description=description)
        board_id = board['id']

        if type == 'basic':
            assigned = self.create_list(board_id=board['id'], name='Assigned')
            complete = self.create_list(board_id=board['id'], name='Complete')

            list_ids = {'assigned': assigned['id'], 'complete': complete['id']}

            return board_id, list_ids

        if type == 'project':

            complete = self.create_list(board_id=board['id'], name='Complete')
            pending = self.create_list(board_id=board['id'], name='Pending')
            in_progress = self.create_list(board_id=board['id'], name='In Progress')
            assigned = self.create_list(board_id=board['id'], name='Assigned')

            list_ids = {'assigned': assigned['id'], 'in_progress': in_progress['id'], 'pending': pending['id'],
                        'complete': complete['id']}

            return board_id, list_ids

        if type == 'design':
            branding = self.create_list(board_id=board['id'], name='Branding')
            websites_collateral = self.create_list(board_id=board['id'], name='Websites & Collateral')
            pending = self.create_list(board_id=board['id'], name='Waiting for Response')
            compliance = self.create_list(board_id=board['id'], name='Compliance')
            complete = self.create_list(board_id=board['id'], name='Complete')

            list_ids = {'branding': branding['id'], 'websites_collateral': websites_collateral['id'],
                        'pending': pending['id'], 'compliance': compliance['id'], 'complete': complete['id']}

            return board_id, list_ids

    def get_board(self, board_id):
        """
        Get board data.

        :param board_id:
            The ID of a board to get
        :return:
            list of dicts
        """

        params = {'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/boards/{board_id}'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_board_labels(self, board_id, limit=1000, fields='all'):

        """
        Get all labels associated with a given board.

        :param board_id:
            The ID of a board to get labels from
        :param fields:
            all or a comma-separated list of label fields
        :param limit:
            integer from 0 to 1000
        :return:
            json object
        """

        url = f'https://api.trello.com/1/boards/{board_id}/labels'

        params = {"fields": fields, "limit": limit, 'key': self.api_key, 'token': self.api_token}
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def add_board_label(self, name, color, board_id):

        """
        Add a label to a given board.

        :param name:
            The name for the card
        :param color:
            The color of the label. One of: yellow, purple, blue, red, green, orange, black, sky, pink, lime, null
        :param board_id:
            The ID of a board to get labels from
        :return:
            response
        """

        params = {"name": name, "color": color, "idBoard": board_id}

        url = f'https://api.trello.com/1/labels'
        response = requests.post(url, params=params)
        data = json.loads(response.content)

        return data

    def get_board_labels_filtered(self, board_id, fields, limit, filter):

        """
        Get labels from a board filtered by a specific criteria.

        :param board_id:
            The ID of a board to get labels from
        :param fields:
            all or a comma-separated list of label fields
        :param limit:
            integer from 0 to 1000
        :param filter:
            One of all, closed, none, open
        :return:
            a list of dicts
        """

        url = f'https://api.trello.com/1/boards/{board_id}/labels/{filter}'

        querystring = {"fields": fields, "limit": limit, 'key': self.api_key, 'token': self.api_token}
        response = requests.get(url, params=querystring)
        data = json.loads(response.content)

        return data

    def get_lists(self, board_id, cards='all', card_fields='all', filter='all', fields='all'):

        """
        Get all lists from a board.

        :param board_id:
            The ID of a board to get lists from
        :param cards:
            all, closed, none, open
        :param card_fields:
            all or a comma-separated list of card fields
        :param filter:
            all, closed, none, open
        :param fields:
            all or a comma-separated list of card fields
        :return:
            a list of dicts
        """

        params = {"cards": cards, "card_fields": card_fields, "filter": filter, "fields": fields, "key": self.api_key,
                  "token": self.api_token}

        url = f'https://api.trello.com/1/boards/{board_id}/lists'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def create_list(self, board_id, name):

        """
        Create a list on a given board.

        :param board_id:
            The ID of a board to get custom fields from
        :param name:
            The name for the list
        :return:
            response
        """

        params = {"name": name, "idBoard": board_id, 'key': self.api_key, 'token': self.api_token}

        url = "https://api.trello.com/1/lists"
        response = requests.post(url, params=params)
        data = json.loads(response.content)

        return data

    def get_board_cards(self, board_id):

        """
        Get all cards from a given board.

        :param board_id:
            The ID of a board to get cards from
        :returns:
            a list of dicts
        """

        params = {'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/boards/{board_id}/cards'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def add_board_member(self, board_id, member_id, type='normal'):

        """
        Adds a member to an existing board.

        :param board_id:
            The ID of a board to add a member to
        :param member_id:
            The ID of a member to add to board
        :param type:
            Type of member role, defaulted to normal
        :return:
            a list of dicts
        """

        params = {'type': type, 'key': self.api_key, 'token': self.api_token}
        headers = {'accept': "application/json"}

        url = f"https://api.trello.com/1/boards/{board_id}/members/{member_id}"
        response = requests.put(url, headers=headers, params=params)
        data = json.loads(response.content)

        return data

    def get_board_custom_fields(self, board_id):

        params = {'key': self.api_key, 'token': self.api_token}

        url = f' https://api.trello.com/1/boards/{board_id}/customFields'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_card_custom_fields(self, card_id):

        params = {'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/cards/{card_id}/customFieldItems'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_member_cards(self, member_id, filter):

        """
        Get all cards from a given member.

        :param member_id:
            The ID of a member to get cards from
        :return:
            a list of dicts
        """

        params = {'filter': filter, 'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/members/{member_id}/cards'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_member_actions(self, member_id):

        """
        Get all actions from a given member.

        :param member_id:
            The ID of a member to get actions from
        :return:
            a list of dicts
        """

        params = {'key': self.api_key, 'token': self.api_token}

        url = f"https://api.trello.com/1/members/{member_id}/actions"
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_list_cards(self, list_id):

        """
        Get all cards from a given list.

        :param list_id:
            The ID of a list to get cards from
        :return:
            a list of dicts
        """

        params = {'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/lists/{list_id}/cards'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_list(self, list_id, fields='all'):

        """
        Get a list and associated data, including cards.

        :param list_id:
            id of list to be accessed.
        :param fields:
            indicator as to whether all fields should be sent or just a subset. Other values include:
        :return:
            json object: list of dicts
        """

        params = {'fields': fields, 'key': self.api_key, 'token': self.api_token}
        url = f"https://api.trello.com/1/lists/{list_id}"
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def get_custom_fields(self, card_id):

        """
        Gets custom field values from a given card.

        :param card_id:
            The ID of a card to get custom fields from
        :return:
            json object: list of dicts
        """

        url = f"https://api.trello.com/1/cards/{card_id}/customFieldItems"

        response = requests.get(url)
        data = json.loads(response.content)

        return data

    def get_card(self, card_id, fields='all', attachments='false', attachment_fields='all', members='false',
                 check_item_states='true', checklists='all', checklist_fields='all', custom_fields='true'):

        """

        """

        url = f"https://api.trello.com/1/cards/{card_id}"

        params = {'fields': fields, 'actions': '', 'attachments': attachments, 'attachment_fields': attachment_fields,
                  'members': members, 'checkItemStates': check_item_states, 'checklists': checklists,
                  'checklist_fields': checklist_fields, 'customFieldItems': custom_fields,
                  'key': self.api_key, 'token': self.api_token}

        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data

    def create_card(self, list_id, name, due=None, pos=None, member_ids=None, labels=None, due_complete=None,
                    url_source=None, source_card=None, keep_source=None, file_source=None, desc=None):

        """
        Creates a new card and associates with given list.

        :param name:
            The name for the card
        :param due:
            A due date for the card
        :param pos:
            The position of the new card. top, bottom, or a positive float
        :param list:
            The ID of the list the card should be created in
        :param member_ids:
            Comma-separated list of member IDs to add to the card
        :param labels:
            Comma-separated list of label IDs to add to the card
        :param due_complete:
            boolean
        :param url_source:
            A URL starting with http:// or https://
        :param source_card:
            The ID of a card to copy into the new card
        :param keep_source:
            If using idCardSource you can specify which properties to copy over all or comma-separated list of:
            attachments,checklists,comments,due,labels,members,stickers
        :param file_source:
            Local file location for upload.
        :param desc:
            The description for the card
        :return:
            response
        """

        url = "https://api.trello.com/1/cards"

        params = {'name': name, 'desc': desc, 'pos': pos, 'due': due, 'dueComplete': due_complete, 'idList': list_id,
                  'idMembers': member_ids, 'idLabels': labels, 'urlSource': url_source, 'fileSource': file_source,
                  'idCardSource': source_card, 'keepFromSource': keep_source, 'key': self.api_key,
                  'token': self.api_token}

        response = requests.post(url, params=params)
        data = json.loads(response.content)

        return data

    def update_card(self, card_id, name=None, due=None, pos=None, list=None, member_ids=None, labels=None,
                    due_complete=None, url_source=None, source_card=None, keep_source=None, file_source=None,
                    desc=None):

        """
        Updates attributes on a given card.

        :param card_id:
            Card id
        :param name:
            The name for the card
        :param due:
            A due date for the card
        :param pos:
            The position of the new card. top, bottom, or a positive float
        :param list:
            The ID of the list the card should be created in
        :param member_ids:
            Comma-separated list of member IDs to add to the card
        :param labels:
            Comma-separated list of label IDs to add to the card
        :param due_complete:
            boolean
        :param url_source:
            A URL starting with http:// or https://
        :param source_card:
            The ID of a card to copy into the new card
        :param keep_source:
            If using idCardSource you can specify which properties to copy over all or comma-separated list of:
            attachments,checklists,comments,due,labels,members,stickers
        :param file_source:
            Local file location for upload.
        :param desc:
            The description for the card
        :return:
            response
        """

        url = f"https://api.trello.com/1/cards/{card_id}"

        params = {'name': name, 'desc': desc, 'pos': pos, 'due': due, 'dueComplete': due_complete, 'idList': list,
                  'idMembers': member_ids, 'idLabels': labels, 'urlSource': url_source, 'fileSource': file_source,
                  'idCardSource': source_card, 'keepFromSource': keep_source, 'key': self.api_key,
                  'token': self.api_token}

        response = requests.put(url, params=params)
        data = json.loads(response.content)

        return data

    def create_checklist(self, card_id, name, checklist_source=None, pos=None):

        """
        Creates a checklist associated with a given card.

        :param card_id:
            The ID of the card that the checklist should be added to.
        :param name:
            The name of the checklist. Should be a string of length 1 to 16384.
        :param checklist_source:
            The ID of a checklist to copy into the new checklist.
        :param pos:
            The position of the checklist on the card. One of: top, bottom, or a positive number.
        :return:
            response
        """

        url = f'https://api.trello.com/1/cards/{card_id}/checklists'

        params = {'name': name, 'idChecklistSource': checklist_source, 'pos': pos, 'key': self.api_key,
                  'token': self.api_token}

        response = requests.post(url, params=params)
        data = json.loads(response.content)

        return data

    def create_checklist_item(self, checklist_id, name, pos='bottom'):

        """
        Creates an item on an existing checklist.

        :param checklist_id:
            ID of a checklist.
        :param name:
            The name of the new check item on the checklist. Should be a string of length 1 to 16384.
        :param pos:
            The position of the check item in the checklist. One of: top, bottom, or a positive number.
        :return:
            response
        """

        url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"

        params = {"name": name, "pos": pos, "checked": "false", 'key': self.api_key, 'token': self.api_token}

        response = requests.post(url, params=params)
        data = json.loads(response.content)

        return data

    def create_webhook(self, id, url, description):

        """
        Creates a new webhook

        :param id:
            id of the record being monitored by the webhook.
        :param url:
            callback url being registered to the webhook.
        :param description:
            description of the webhook being registered.
        :return:
            response code
        """

        params = {"key": f"{self.api_key}",
                  "callbackURL": url,
                  "idModel": id,
                  "description": description}

        url = f'https://api.trello.com/1/tokens/{self.api_token}/webhooks/'
        response = requests.post(url, params=params)
        data = json.loads(response.content)

        return data

    def update_webhook(self, webhook_id, id=None, url=None, description=None):

        """
        Updates an existing webhook.

        :param webhook_id:
            id of the registered webhook being updated.
        :param id:
            id of the record associated with the webhook in question.
        :param url:
            registered callback url for webhook.
        :param description:
            Description of the webhook being updated; can be updated as a part of this call.
        :return:
            response code
        """

        params = {"callbackURL": url,
                  "idModel": id,
                  "description": description,
                  'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/webhooks/{webhook_id}'
        response = requests.put(url, params=params)
        data = json.loads(response.content)

        return data

    def delete_webhook(self, webhook_id):

        """
        Deletes an active webhook.

        :param webhook_id:
            id of active webhook to be deleted
        :return:
            response code
        """
        params = {'key': self.api_key, 'token': self.api_token}

        url = f'https://api.trello.com/1/webhooks/{webhook_id}'
        response = requests.delete(url, params=params)
        data = json.loads(response.content)

        return data

    def get_all_webhooks(self):

        """
        Retrieves a list of all registered and active webhooks

        :return:

        """

        params = {'key': self.api_key}
        url = f'https://api.trello.com/1/tokens/{self.api_token}/webhooks'
        response = requests.get(url, params=params)
        data = json.loads(response.content)

        return data
