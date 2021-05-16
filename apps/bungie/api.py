import datetime
import json
import logging
import requests


class BungieException(Exception):
    pass


class BungieAPI:
    SUCCESS_CODES = [200, 201, 204]
    __logger = None

    def __init__(self, key):
        self.__logger = logging.getLogger(__name__)
        self.host = 'https://www.bungie.net/platform/'
        self.headers = {
            'Content-Type': 'application/json'
        }
        if key:
            self.headers['X-API-Key'] = str(key)
        else:
            raise BungieException('No key provided')

    def __send(self, method, path, data=None, params=None, data_json=None):
        url = self.host + path

        try:
            response = requests.request(method=method.lower(), url=url, data=data, json=data_json, params=params,
                                        verify=False, headers=self.headers)
        except requests.exceptions.Timeout:
            self.__logger.error('Bungie API timeout')
            raise BungieException('Timeout')
        except requests.exceptions.RequestException as e:
            raise BungieException(f'Wrong request: {str(e)}')

        if response.status_code not in self.SUCCESS_CODES:
            self.__logger.error(response.content)
            raise BungieException(str(response.content, 'utf-8'))

        return response

    def get_clan_members(self, clan_id):
        response = self.__send('get', f'groupv2/{str(clan_id)}/members/')
        response_json = json.loads(response.content)
        result = []

        data = response_json.get('Response', None)
        if data:
            data = data.get('results', [])
            for user in data:
                user_info = user.get('destinyUserInfo', None)
                if user_info:
                    if user.get("lastOnlineStatusChange"):
                        last_online = datetime.datetime.fromtimestamp(int(user.get("lastOnlineStatusChange")))
                    else:
                        last_online = datetime.datetime.now()

                    if user.get("isOnline"):
                        last_online = datetime.datetime.now()

                    result.append({
                        'is_online': user.get("isOnline"),
                        'membership_id': user_info.get("membershipId"),
                        'display_name': user_info.get("LastSeenDisplayName"),
                        'last_online': last_online
                                   })
        return result

    def get_profile(self, membership_id):
        response = self.__send('get', f'destiny2/1/profile/{str(membership_id)}')
        result = json.loads(response.content)







