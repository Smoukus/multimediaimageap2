import math

from kivy_garden.mapview import MapView, MapMarker
from kivy.app import App
from kivy.utils import platform
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from plyer import gps, notification
from android.permissions import Permission, request_permissions
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.clock import mainthread
from kivy.properties import StringProperty, NumericProperty
from geopy import distance
from kivy.uix.screenmanager import ScreenManager, Screen

class StartScreen(Screen):
    def build(self):
        pass

class MapScreen(Screen):

    boat = None
    anchor = None
    latitude_anchor = NumericProperty(48.47197966594304)
    longitude_anchor = NumericProperty(7.953795063926035)

    latitude_boat = NumericProperty(48.47197966594304)
    longitude_boat = NumericProperty(7.953795063926035)
    radius = StringProperty('10')

    def addRadius(self):
        self.radius = str(int(self.radius) + 1)

    def subRadius(self):
        if (int(self.radius) - 1 == 0):
            return None
        self.radius = str(int(self.radius) - 1)
       
    def equalizeLatLon(self, accuracy, direction):
        r_earth = 6378137
        if direction == 'right' or direction == "left":
            return (accuracy / r_earth) * (180 / math.pi) / math.cos(self.latitude_anchor * math.pi / 180);
        elif direction == 'up' or direction == "down":
            return (accuracy / r_earth) * (180 / math.pi);
        else:
            return accuracy

    def moveAnchor(self, direction):
        if self.anchor != None:
            self.manager.get_screen("mapScreen").ids.map.remove_marker(self.anchor)
        step_size = 1
        if direction == 'up':
            self.latitude_anchor = self.latitude_anchor + self.equalizeLatLon(step_size, direction)
            print(self.latitude_anchor)
        elif (direction == 'down'):
            self.latitude_anchor = self.latitude_anchor - self.equalizeLatLon(step_size, direction)
        elif (direction == 'left'):
            self.longitude_anchor = self.longitude_anchor - self.equalizeLatLon(step_size, direction)
        elif (direction == 'right'):
            self.longitude_anchor = self.longitude_anchor + self.equalizeLatLon(step_size, direction)
        self.anchor = MapMarker(lat=self.latitude_anchor, lon=self.longitude_anchor, source='icons/anchor.png')
        self.manager.get_screen("mapScreen").ids.map.add_marker(self.anchor)
        self.calculate_distance()

    def generateNewBoat(self):
        if self.boat != None:
            self.manager.get_screen("mapScreen").ids.map.remove_marker(self.boat)
        self.boat = MapMarker(lat=self.latitude_boat, lon=self.longitude_boat, source='icons/boat.png')
        self.manager.get_screen("mapScreen").ids.map.add_marker(self.boat)
        self.manager.get_screen("mapScreen").ids.map.remove_marker(self.anchor)
        self.anchor.lon = self.boat.lon
        self.longitude_anchor = self.boat.lon
        self.latitude_anchor = self.boat.lat
        self.manager.get_screen("mapScreen").ids.map.add_marker(self.anchor)

    def refreshVariables(self):
        settingsRadius = App.get_running_app().root.get_screen("settingsScreen").ids.settingsRadius
        settingsRadius.text = self.radius

        settingsLon = App.get_running_app().root.get_screen("settingsScreen").ids.settingsLon
        settingsLon.text = str(self.longitude_boat)

        settingsLat = App.get_running_app().root.get_screen("settingsScreen").ids.settingsLat
        settingsLat.text = str(self.latitude_boat)

    def calculate_distance(self):
        kilo = distance.distance((self.latitude_boat,self.longitude_boat), (self.latitude_anchor,self.longitude_anchor)).meters
     

    # Callback-Funktion für die GPS-Daten
    @mainthread
    def on_gps_location(self, **kwargs):
        self.latitude_boat = kwargs['lat']
        self.longitude_boat = kwargs['lon']
        map_widget = App.get_running_app().root.get_screen("mapScreen").ids.map
        map_widget.lat = self.latitude_boat
        map_widget.lon = self.longitude_boat
        map_widget.center_on(self.latitude_boat, self.longitude_boat)

    # Starten vom GPS-Service
    def start(self, minTime, minDistance):
        gps.start(minTime, minDistance)
    
    # Stoppen vom GPS-Service
    def stop(self):
        gps.stop()
    
    def on_pause(self):
        gps.stop()
        return True
    
    def on_resume(self):
        gps.start(5000, 0)
        pass

class SettingsScreen(Screen):
    def build(self):
        pass
       
class AppScreenManager(ScreenManager):
    pass

class AnkeralarmApp(App):
    mapscreen = MapScreen()
    isAlarmActive = False
    navButtonDefaultColor = (0, 200, 200, 0.8)
    navButtonPressedColor = (0, 200, 200, 0.5)
    currentScreen = ""

    playButtonStandbyColor = (0, 200, 0, 0.8)
    playButtonActiveColor = (200, 0, 0, 0.8)

    def build(self):
        #GPS Aktivieren nur, wenn man auf Android unterwegs ist
        if platform == 'android':
            # Berechtigungen fuer Android
            def callback(permission, results):
                if all([res for res in results]):
                    print('Alle Berechtigungen freigegeben')
                else:
                    print('Nicht alle Berechtigungen freigegeben')
            request_permissions([Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION], callback)

            # Verbindung mit dem GPS-Service
            gps.configure(on_location=self.mapscreen.on_gps_location)

        self.title = "Ankeralarm"
        self.icon = 'icons/appicon.png'
        return Builder.load_file("main.kv")

    def on_nav_button_press(self,button):
        button.background_color = (1, 200, 200, 0.8)

    def on_nav_button_release(self,button):
        button.background_color = (1, 200, 200, 0.5)

    def toggle_play_button_press(self):
        playButtonImage1 = App.get_running_app().root.get_screen("mapScreen").ids.mapPlayButtonImage
        playButtonImage2 = App.get_running_app().root.get_screen("settingsScreen").ids.settingsPlayButtonImage

        playButton1 = App.get_running_app().root.get_screen("mapScreen").ids.mapPlayButton
        playButton2 = App.get_running_app().root.get_screen("settingsScreen").ids.settingsPlayButton

        if self.isAlarmActive:
            self.isAlarmActive = False
            playButton1.background_color = self.playButtonStandbyColor
            playButton2.background_color = self.playButtonStandbyColor
            playButtonImage1.source = "./icons/play-button-arrowhead.png"
            playButtonImage2.source = "./icons/play-button-arrowhead.png"
       
        else:
            self.isAlarmActive = True
            playButton1.background_color = self.playButtonActiveColor
            playButton2.background_color = self.playButtonActiveColor
            playButtonImage1.source = "./icons/pause.png"
            playButtonImage2.source = "./icons/pause.png"
    
    def toggle_button_color_on_screen_change(self, button, currentScreen):
        print(button.parent.parent)
    
if __name__ == '__main__':
    AnkeralarmApp().run()