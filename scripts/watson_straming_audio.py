#!/usr/bin/env python

from ws4py.client.threadedclient import WebSocketClient
import base64
import json
import ssl
import subprocess
import threading
import time
import rospy
from std_msgs.msg import String


"""
Send audio stream to IBM Watson Speech recognition engine
using the arecord 'hack' via websocket.
Publish results on a std_msgs/String topic,
'/watson_stt/heard' by default.

Needed:
sudo pip install ws4py

Author: Sammy Pfeiffer
"""


class SpeechToTextClient(WebSocketClient):
    def __init__(self, recognized_callback):
        # Note that the documentation says another URL, this is the correct one
        self.ws_url = "wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize"
        username = "c9201979-fa56-4281-8628-940e6f35fb3a"
        password = "DdUs6NEJPpnm"
        auth_string = "%s:%s" % (username, password)
        self.base64string = base64.encodestring(auth_string).replace("\n", "")
        self.recognized_callback = recognized_callback
        self.listening = False

        try:
            WebSocketClient.__init__(self, self.ws_url,
                                     headers=[("Authorization",
                                               "Basic %s" % self.base64string)])
            self.connect()
        except Exception as e:
            print "Failed to open WebSocket."
            print e

    def opened(self):
        # Note that the audio must be of rate 16000
        # Note that inactivity_timeout -1 disables the 30s default stopping
        self.send('{"action": "start", "content-type": "audio/l16;rate=16000","interim_results": true, "timestamps": true, "inactivity_timeout":-1}')
	print "start"
        self.stream_audio_thread = threading.Thread(target=self.stream_audio)
        self.stream_audio_thread.start()

    def received_message(self, message):
        message = json.loads(str(message))
        if "state" in message:
            if message["state"] == "listening" and not self.listening:
                self.listening = True
        elif "results" in message:
            self.recognized_callback(message["results"])
            # To keep listening we need to send an empty payload
            # http://www.ibm.com/watson/developercloud/doc/speech-to-text/websockets.shtml#WSstop
	    #self.send(bytearray(''), binary=True)
        elif "error" in message:
            # We are currently asking for inactivity_timeout infinite
            # but
            # To keep it open we could send every... 25s this, instead:
            # self.send('{"action": "no-op"}')
            pass
        print "Message received: " + str(message)

    def stream_audio(self):
        while not self.listening:
	    #print"waiting"
            time.sleep(0.01)

        # reccmd = ["arecord", "-f", "S16_LE", "-r", "16000", "-t", "raw"]
        # For CHIP
        reccmd = ["arecord", "-D", "plughw:2,0",
                  "-f", "S16_LE",
                  "-r", "16000",
                  "-t", "raw"]
        p = subprocess.Popen(reccmd, stdout=subprocess.PIPE)

        while self.listening:
	    
            data = p.stdout.read(1024)

            try:
		#print "listening"
                self.send(bytearray(data), binary=True)
            except ssl.SSLError as e:
                print "error: " + str(e)

        #p.kill()

    def close(self, *args):
        self.listening = False
        self.stream_audio_thread.join()
        WebSocketClient.close(self)


class WatsonSTTPub(object):
    def __init__(self):
        self.stt_client = SpeechToTextClient(self.recognized_cb)
        self.pub = rospy.Publisher('~heard', String, queue_size=1)

    def recognized_cb(self, results):
	print len(results)
        print results
        # results looks like:
        # [{u'alternatives': [{u'confidence': 0.982, u'transcript': u'hello '}], u'final': True}]
        sentence = results[0]["alternatives"][0]["transcript"]
        completion = results[0]["final"]
	print type(completion)
	if completion == 1:
        	self.pub.publish(String(sentence))
        	print '\n    Heard:   "' + str(sentence) + '"\n'
		print completion

    def __del__(self):
        self.stt_client.close()


if __name__ == '__main__':
    rospy.init_node('watson_stt')
    wsttp = WatsonSTTPub()
    rospy.spin()

