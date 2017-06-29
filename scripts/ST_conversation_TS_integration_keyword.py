import time
import rospy
import json
import pyaudio
import wave
import timeit
import base64
import ssl
import subprocess
import threading
import os
import signal
import psutil

from ws4py.client.threadedclient import WebSocketClient
from os.path import join, dirname
from watson_developer_cloud import TextToSpeechV1
from watson_developer_cloud import ConversationV1
from std_msgs.msg import String
from playsound import playsound
a=0

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
        self.send('{"action": "start", "content-type": "audio/l16;rate=16000","interim_results": true, "timestamps": true, "inactivity_timeout":-1, "keywords":["what", "name", "hello", "welcome","thank you", "bye"], "keywords_threshold": 0.55}')
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
	global a
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
	psProcess = psutil.Process(pid=p.pid)

        while self.listening :
		#print a
	   	if a == 1:
			#psProcess.suspend()
			os.kill(p.pid, signal.SIGSTOP)
		else:
			#psProcess.resume()
			os.kill(p.pid, signal.SIGCONT)
			data = p.stdout.read(1024)
		
            	try:
		
                	self.send(bytearray(data), binary=True)
            	except ssl.SSLError as e:
                	print "error: " + str(e)

        #p.kill()

    def close(self, *args):
        self.listening = False
        self.stream_audio_thread.join()
        WebSocketClient.close(self)





class WatsonSTTPub(object):
    global a
    def __init__(self):
        self.stt_client = SpeechToTextClient(self.recognized_cb)
        self.pub = rospy.Publisher('~heard', String, queue_size=1)
	


    def play_audio(self,audio):
	global a
	#os.kill(p.pid, signal.SIGSTOP)
	chunk = 1024
	wf = wave.open(audio, 'rb')
	t = pyaudio.PyAudio()
	a =1
	
	stream = t.open(
		format = t.get_format_from_width(wf.getsampwidth()),
		channels = wf.getnchannels(),
		rate = wf.getframerate(),
		output = True)
	data = wf.readframes(chunk)
	
	while data != '':
		stream.write(data)
		data = wf.readframes(chunk)
	
	a=0	

	
	print a
	#os.kill(programID.pid, signal.SIGCONT)
	stream.close()
	t.terminate()

	
    
    def recognized_cb(self, results):
	
        print results
        # results looks like:
        # [{u'alternatives': [{u'confidence': 0.982, u'transcript': u'hello '}], u'final': True}]
        sentence = results[0]["alternatives"][0]["transcript"]
        completion = results[0]["final"]
	
	
	if completion == 1:
		if results[0]["alternatives"][0]["confidence"]>0.5:
			audio = "answer.wav"
			self.play_audio(audio)
			
			self.pub.publish(String(sentence))

        	print '\n    Heard:   "' + str(sentence) + '"\n'
		print  results[0]["alternatives"][0]["confidence"]
		print completion

    def __del__(self):
        self.stt_client.close()






	

if __name__ == '__main__':
	rospy.init_node('watson_stt')
	wsttp = WatsonSTTPub()
	
	rospy.spin()
