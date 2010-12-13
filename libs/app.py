import mc, time, re, Func, sys, os
from threading import Thread
from urllib import quote
from decimal import *
from BeautifulSoup import BeautifulSoup

class Karaoke(object):
    def __init__(self):
        self.time_lyr = []
        self.text_lyr = []
        self.player = mc.GetPlayer()
        self.trackid = None
        self.coverart = None
        self.title = mc.GetInfoString("MusicPlayer.Title")
        self.artist = mc.GetInfoString("MusicPlayer.Artist")
		self.apikey = ''
        self.error = 3
        self.view = 0

    def GetTrackid(self):
        url_id = 'http://api.musixmatch.com/ws/1.1/track.search?apikey=' + self.apikey + '&format=xml&q_artist=' + str(quote(self.artist)) + '&q_track=' + str(quote(self.title)) + '&page_size=1&f_has_lyrics=1'
        data = Func.GetCached(url_id, 3600)
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")
        if soup.message.header.status_code.contents[0] == '200':
            try:
                self.trackid = soup.message.body.track_id.contents[0]
            except:
                self.error = 2
        else:
            self.error = 2

    def GetSub(self):
        self.time_lyr = []
        self.text_lyr = []
        urlsub = 'http://api.musixmatch.com/ws/1.1/track.subtitle.get?apikey=' + self.apikey + '&format=xml&track_id=' + str(self.trackid)
        data = Func.GetCached(urlsub, 3600)
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")
        if soup.message.header.status_code.contents[0] == '200':
            lyric = soup.message.body.subtitle.subtitle_body.contents[0]
            lyrics = lyric.split('\r\n')
            exclude = '[la:'
            lyrics = [item for item in lyrics if not item.startswith(exclude)]
            for clean in lyrics:
                try:
                    time = re.compile('\[(.*?)\]', re.DOTALL + re.IGNORECASE).search(clean).group(1)
                    total_time = int(time[:2]) * 60 + Decimal(time[3:])
                    self.time_lyr.append(total_time)
                    text = re.compile('\](.*?)$', re.DOTALL + re.IGNORECASE).search(clean).group(1)
                    self.text_lyr.append(text)
                except:
                    self.error = self.error
        else:
            self.error = 2

    def GetLyrics(self):
        self.text_lyr = []
        urlsub = 'http://api.musixmatch.com/ws/1.1/track.lyrics.get?apikey=' + self.apikey + '&format=xml&track_id=' + str(self.trackid)
        data = Func.GetCached(urlsub, 3600)
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")
        if soup.message.header.status_code.contents[0] == '200':
            try:
                lyric = soup.message.body.lyrics.lyrics_body.contents[0] + '\n .........{{END}}........... \n'
                self.text_lyr = lyric.split('\n')
            except:
                self.error = self.error
        else:
            self.error = 2

    def _error(self):
        list = mc.GetActiveWindow().GetList(51)
        list_items = mc.ListItems()
        list_item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
        if self.error == 1:
            list_item.SetLabel('Start first a song or playlist!')
        else:
            list_item.SetLabel('No lyrics found for this song...')
        list_items.append(list_item)
        list.SetItems(list_items)
        mc.GetActiveWindow().GetControl(101).SetFocus()
        st = _end_in_thread()
        st.start()
                        
    # Play item with either Boxee's action menu, our MF's. #
    def Start(self):
        mc.ShowDialogWait()
	print str(mc.GetActiveWindow())
	print str(mc.GetWindow(14444))
        if self.player.IsPlaying() != 1:
            self.error = 1
            
        if self.error > 2:
            self.GetTrackid()
            if self.error > 2:
                self.GetSub()
                if self.error > 2:
                    list = mc.GetActiveWindow().GetList(51)
                    list_items = mc.ListItems()
                    for i in range(len(self.time_lyr)):
                        list_item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                        list_item.SetLabel(str(self.text_lyr[i].encode('utf-8')))
                        list_item.SetProperty('icon', 'lrc.png')
                        list_items.append(list_item)
                        pt = _lyrics_in_thread(i, self.time_lyr[i])
                        pt.start()
                    st = _end_in_thread()
                    st.start()
                    list.SetItems(list_items)
                else:
                    self.error = 3
                    self.GetLyrics()
                    if self.error > 2:
                        list = mc.GetActiveWindow().GetList(51)
                        list_items = mc.ListItems()
                        for i in range(len(self.text_lyr)):
                            list_item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                            list_item.SetLabel(str(self.text_lyr[i].encode('utf-8')))
                            list_item.SetProperty("icon", '')
                            list_items.append(list_item)
                        st = _end_in_thread()
                        st.start()
                        list.SetItems(list_items)
                        list.SetFocusedItem(0)
                    else:
                        self._error()
            else:
                self._error()
        else:
            self._error()

        mc.HideDialogWait()


class _lyrics_in_thread(Thread):
    # Define class vars. #
    def __init__ (self, index, insert):
        Thread.__init__(self)
        self.index = index
        self.player = mc.GetPlayer()
        self.title = mc.GetInfoString("MusicPlayer.Title")
        self.insert = insert
        self.list = mc.GetActiveWindow().GetList(51)
        self.list2 = mc.GetActiveWindow().GetControl(101)

    # Run() method required for Thread. #
    def run(self):
        if int(round(self.player.GetTime(), 2)*100) < int(self.insert*100):
            # Loop the player until we have reached the play limit (in seconds). #
            while self.player.IsPlaying():
                if self._window() == 0:
                    break
                elif int(round(self.player.GetTime(), 2)*100) > (self.insert*100):
                    self.list.SetFocusedItem(self.index)
                    self.list2.SetFocus()
                    break
                elif mc.GetInfoString("MusicPlayer.Title") != self.title:
                    break
                else:
                    time.sleep(1)
    def _window(self):
        try:
            mc.GetWindow(14444)
        except:
            return False

class _end_in_thread(Thread):
    # Define class vars. #
    def __init__ (self):
        Thread.__init__(self)
        self.player = mc.GetPlayer()
        self.title = mc.GetInfoString("MusicPlayer.Title")

    # Run() method required for Thread. #
    def run(self):
        while self.player.IsPlaying():
            if self._window() == 0:
                break
            elif mc.GetInfoString("MusicPlayer.Title") != self.title:
                a = Karaoke()
                a.Start()
                break
            else:
                time.sleep(1)
    def _window(self):
        try:
            mc.GetWindow(14444)
        except:
            return False


