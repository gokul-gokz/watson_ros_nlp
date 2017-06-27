# coding=utf-8
import time
import rospy
import json
import pyaudio
import wave
import timeit
from conversation import *


from os.path import join, dirname
from watson_developer_cloud import TextToSpeechV1
from std_msgs.msg import String
from playsound import playsound


def callback(data):
	

	#rospy.loginfo(rospy.get_caller_id() + "I heard %s", data.data)

	#calculate the time of block
	start_time = timeit.default_timer()

	text_to_speech = TextToSpeechV1(username='a4f70d58-88d9-4bf1-8baa-47deffa4cd76',password='hwCW1fZQysmv',x_watson_learning_opt_out=True)
        # Optional flag

	#print(json.dumps(text_to_speech.voices(), indent=2))

	with open('data.txt') as json_file:  
    		response = json.load(json_file)

	with open(join(dirname(__file__), 'answer.wav'), 'wb') as audio_file:
    		audio_file.write(text_to_speech.synthesize(data.data, accept='audio/wav', voice="en-US_AllisonVoice"))

	play_audio()

	elapsed = timeit.default_timer() - start_time

	print "time taken"

	print elapsed
	#print(json.dumps(text_to_speech.pronunciation('Watson', pronunciation_format='spr'), indent=2))

	#print(json.dumps(text_to_speech.customizations(), indent=2))

	


def text_to_speech():
	
	
  
	rospy.init_node('text_to_speech', anonymous=True)

	rospy.Subscriber("Robot_response", String, callback)

	rospy.spin()

def play_audio():

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
	

if __name__ == '__main__':
	text_to_speech()




