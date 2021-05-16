from operator import itemgetter

from django.shortcuts import render

from apps.bungie.api import BungieAPI


def index(request):
    api = BungieAPI('f31cdc51a7b74c2398cf3dae6f5cc55f')
    members = api.get_clan_members(2135560)

    members = sorted(members, key=itemgetter('last_online'), reverse=True)

    return render(request, 'index.html', {'data': members})
