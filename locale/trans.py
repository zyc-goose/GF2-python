#!/usr/bin/python

import wx
import gettext

class Translation(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(220, 100))

        panel = wx.Panel(self, -1)

        mylocale = wx.Locale()
        mylocale.AddCatalogLookupPathPrefix('.')
        mylocale.AddCatalog('zh_CN')

        _ = wx.GetTranslation

        wx.StaticText(panel, -1, _("Run"), (10, 10))
        #wx.StaticText(panel, -1, wx.GetTranslation('hello'), (10, 10))

        self.Centre()
        self.Show(True)

self.presLan_fr = gettext.translation("trans", "./locale", languages=['fr'])
self.presLan_fr.install()
self.locale = wx.Locale(wx.LANGUAGE_FRENCH)
locale.setlocale(locale.LC_ALL, 'FR')


app = wx.App()
Translation(None, -1, 'Translation')
app.MainLoop()