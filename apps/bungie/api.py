import datetime
import json
import logging
from collections import OrderedDict
from operator import itemgetter

import requests
import urllib3

from bungie.models import Profile, Raid, Activity
from bungie.utils import plural_days

class BungieException(Exception):
    pass


class BungieAPI:
    SUCCESS_CODES = [200, 201, 204]
    CLASS_TYPE = (
        (0, 'Titan'),
        (1, 'Hunter'),
        (2, 'Warlock')
    )
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
        urllib3.disable_warnings()
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

                    last_online = datetime.datetime.now()

                    if user.get("lastOnlineStatusChange") and not user.get("isOnline"):
                        last_online = datetime.datetime.fromtimestamp(int(user.get("lastOnlineStatusChange")))

                    delta = datetime.datetime.now() - last_online
                    if delta.days == 0:
                        last_online_text = 'сегодня'
                    elif delta.days == 1:
                        last_online_text = 'вчера'
                    else:
                        last_online_text = f'{delta.days} {plural_days(delta.days)} назад'

                    chars = []
                    res_raids = {}

                    profile = self.get_profile(user_info.get("membershipId"), user_info.get('membershipType'))
                    profile_data = profile.get('Response', None)
                    if profile_data:

                        characters = profile_data.get('characters', None)
                        if characters:
                            if characters.get('privacy') != 1:
                                print(user_info.get("membershipId"))
                                continue
                            characters_data = characters.get('data', None)


                            for character in characters_data:
                                character = characters_data.get(character)
                                chars.append({
                                    'character_id': character.get('characterId'),
                                    'light': character.get('light'),
                                    'minutes_played_total': character.get('minutesPlayedTotal'),
                                    'class': dict(self.CLASS_TYPE).get(int(character.get('classType'))),
                                    'emblem_path': character.get('emblemPath'),
                                    'emblem_background_path': character.get('emblemBackgroundPath'),
                                })

                                raid_stats = self.get_activity_history(user_info.get("membershipId"), character.get('characterId'), 4,  user_info.get('membershipType'))

                                if not raid_stats:
                                    continue

                                raids = raid_stats.get('Response', None).get('activities', None)
                                if raids:

                                    for raid in raids:
                                        details = raid.get('activityDetails', None)
                                        raid_id = details.get('referenceId')

                                        complete = raid.get('values').get('completed').get('basic').get('displayValue')

                                        if complete == 'Yes':
                                            raid_data = self.get_activity_by_hash(raid_id)
                                            raid_props = raid_data.get('displayProperties')
                                            if raid_props.get('name') in res_raids:
                                                res_raids[raid_props.get('name')]['completion'] += 1
                                            else:
                                                res_raids[raid_props.get('name')] = {
                                                    'name': raid_props.get('name'),
                                                    'completion': 1,
                                                    'icon': raid_props.get('icon'),
                                                    'has_icon': raid_props.get('hasIcon'),
                                                    'image': raid_data.get('pgcrImage')
                                                }

                    result.append({
                        'is_online': user.get("isOnline"),
                        'membership_id': user_info.get("membershipId"),
                        'display_name': user_info.get("LastSeenDisplayName"),
                        'last_online': last_online,
                        'last_online_text': last_online_text,
                        'lost_warning': True if delta.days > 30 else False,
                        'characters': chars,
                        'raids': OrderedDict(sorted(res_raids.items()))
                    })
        return result

    def get_profile(self, membership_id, membership_type):
        profile, created = Profile.objects.get_or_create(membership_id=membership_id)

        if created:
            response = self.__send('get', f'Destiny2/{str(membership_type)}/Profile/{str(membership_id)}', params={'components': 200})
            profile.content = json.loads(response.content)
            profile.save()

        return profile.content

    def get_activity_history(self, membership_id, char_id, mode, membership_type):
        activity, created = Activity.objects.get_or_create(char_id=char_id, mode_id=mode)
        if created:
            try:
                response = self.__send('get', f'Destiny2/{str(membership_type)}/Account/{str(membership_id)}/Character/{str(char_id)}/Stats/Activities/', params={'count': 100, 'mode': mode})
                activity.content = json.loads(response.content)
                activity.save()
            except BungieException as e:
                activity.delete()
                return False

        return activity.content

    def get_activity_by_hash(self, activity_id):
        raid, created = Raid.objects.get_or_create(raid_id=activity_id)
        if created:
            response = self.__send('get', f'Destiny2/Manifest/DestinyActivityDefinition/{str(activity_id)}/')
            raid.content = json.loads(response.content)
            raid.save()
        return raid.content.get('Response')







