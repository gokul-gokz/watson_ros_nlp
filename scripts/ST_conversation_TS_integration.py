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

from ws4py.client.threadedclient import WebSocketClient
from os.path import join, dirname
from watson_developer_cloud import TextToSpeechV1
from watson_developer_cloud import ConversationV1
from std_msgs.msg import String
from playsound import playsound

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
	


    def play_audio(self):

	chunk = 1024
	wf = wave.open('answer.wav', 'rb')
	p = pyaudio.PyAudio()

	stream = p.open(
		format = p.get_format_from_width(wf.getsampwidth()),
		channels = wf.getnchannels(),
		rate = wf.getframerate(),
		output = True)
	data = wf.readframes(chunk)

	while data != '':
		stream.write(data)
		data = wf.readframes(chunk)

	stream.close()
	p.terminate()

	
    def text_to_speech(self,answer):
	text_to_speech = TextToSpeechV1(username='a4f70d58-88d9-4bf1-8baa-47deffa4cd76',password='hwCW1fZQysmv',x_watson_learning_opt_out=True)
	
	start1 = time.time()
	with open(join(dirname(__file__), 'answer.wav'), 'wb') as audio_file:
    		audio_file.write(text_to_speech.synthesize(answer, accept='audio/wav', voice="en-US_AllisonVoice"))
	self.play_audio()
	print "ready"
	T3 = time.time() -start1
	print "TS_node_time"
	print T3
	

    def recognized_cb(self, results):
	
        print results
        # results looks like:
        # [{u'alternatives': [{u'confidence': 0.982, u'transcript': u'hello '}], u'final': True}]
        sentence = results[0]["alternatives"][0]["transcript"]
        completion = results[0]["final"]
	
	print type(completion)
	conversation = ConversationV1(
 	 username='24c24760-7d8c-4862-afab-955a5ca63511',
  	 password='2WvceTeJKH3g',
  	 version='2017-05-26'
        )
	context = {}
	start = time.time()
	if completion == 1:
		if results[0]["alternatives"][0]["confidence"]>0.5:
			#self.play_audio()
			workspace_id = 'f8c86853-434f-4588-baed-226a26f855c0'
			T1 = time.time() -start
			print "ST_node_time"
			print T1
			response = conversation.message(workspace_id=workspace_id,message_input={'text':sentence},context=context)
			T2 = time.time() -start
			print "Conversation_node_time"
			print T2
			if(len(response[u'output'][u'text']) == 0):
				answer = "Pardon. Can you repeat"
				self.text_to_speech(answer)
		
			else:
				answer = response[u'output'][u'text'][0]
				self.text_to_speech(answer)
		
	 
			print answer        		

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
