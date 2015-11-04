'''
    ustvnow XBMC Plugin
    Copyright (C) 2011 t0mm0

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import Addon
import cookielib
import os
import re
import urllib, urllib2

class Ustvnow:
    __BASE_URL = 'http://lv2.ustvnow.com'
    def __init__(self, user, password):
        self.user = user
        self.password = password
                    
    def get_channels(self, quality=1, stream_type='rtmp'):
        self._login()
        html = self._get_html('iphone_ajax', {'tab': 'iphone_playingnow', 
                                              'token': self.token})
        channels = []
        for channel in re.finditer('class="panel".+?title="(.+?)".+?src="' + 
                                   '(.+?)".+?class="nowplaying_item">(.+?)' +
                                   '<\/td>.+?class="nowplaying_itemdesc".+?' +
                                   '<\/a>(.+?)<\/td>.+?href="(.+?)"',
                                   html, re.DOTALL):
            name, icon, title, plot, url = channel.groups()
            if not url.startswith('http'):
                now = {'title': title, 'plot': plot.strip()}
                if name == 'CW' or name == 'PBS' or name == 'My9':
                  my_quality = quality
                else: my_quality = quality+1
                url = '%s%s%d' % (stream_type, url[4:-1], my_quality)
                channels.append({'name': name, 'url': url, 
                               'icon': icon, 'now': now})
                print "name=<"+name+">/n"
        return channels        

    def get_recordings(self, quality=1, stream_type='rtmp'):
        self._login()
        html = self._get_html('iphone_ajax', {'tab': 'iphone_viewdvrlist'})
        schedule_index = html.find('Scheduled')
        if schedule_index > 0:
            html = html[0:schedule_index]
        recordings = []
        for r in re.finditer('class="panel".+?title="(.+?)".+?src="(.+?)".+?' +
                             'class="nowplaying_item">(.+?)<\/td>.+?(?:<\/a>' +
                             '(.+?)<\/td>.+?)?vertical-align:bottom.+?">.+?(Recorded.+?)' +
                             '<\/div>.+?"(rtsp.+?)".+?"(iphone_ajax.+?)"', 
                             html, re.DOTALL):
            chan, icon, title, plot, rec_date, url, del_url = r.groups()
            rec_date = rec_date.replace('\n', ' ').replace('\r', '').replace('\t', '')
            url = '%s%s%s' % (stream_type, url[4:-7], 
                              ['350', '650', '950'][quality])
            if plot:
                plot = plot.strip()
            else:
                plot = ''
            recordings.append({'channel': chan,
                               'stream_url': url,
                               'title': title,
                               'plot': plot,
                               'rec_date': rec_date.strip(),
                               'icon': icon,
                               'del_url': del_url
                               })
        return recordings
    
    def delete_recording(self, del_url):
        html = self._get_html(del_url)
        print html
    
    def _build_url(self, path, queries={}):
        if queries:
            query = Addon.build_query(queries)
            return '%s/%s?%s' % (self.__BASE_URL, path, query) 
        else:
            return '%s/%s' % (self.__BASE_URL, path)

    def _fetch(self, url, form_data=False):
        if form_data:
            Addon.log('posting: %s %s' % (url, str(form_data)))
            req = urllib2.Request(url, form_data)
        else:
            Addon.log('getting: ' + url)
            req = url
        try:
            response = urllib2.urlopen(url)
            return response
        except urllib2.URLError, e:
            Addon.log(str(e), True)
            return False
        
    def _get_html(self, path, queries={}):
        html = False
        url = self._build_url(path, queries)

        response = self._fetch(url)
        if response:
            html = response.read()
        else:
            html = False
        
        return html

    def _login(self):
        Addon.log('logging in') 
        self.token = None
        self.cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        
        urllib2.install_opener(opener)
        url = self._build_url('iphone_login', {'username': self.user, 
                                               'password': self.password})
        response = self._fetch(url)
        #response = opener.open(url)
        
        for cookie in self.cj:
            print '%s: %s' % (cookie.name, cookie.value)
            if cookie.name == 'token':
                self.token = cookie.value
