import time
import rospy
import json
import pyaudio
import wave
import timeit

from os.path import join, dirname
from watson_developer_cloud import TextToSpeechV1
from watson_developer_cloud import ConversationV1
from std_msgs.msg import String
from playsound import playsound

conversation = ConversationV1(
  username='24c24760-7d8c-4862-afab-955a5ca63511',
  password='2WvceTeJKH3g',
  version='2017-05-26'
)

def text_to_speech(answer):
	text_to_speech = TextToSpeechV1(username='a4f70d58-88d9-4bf1-8baa-47deffa4cd76',password='hwCW1fZQysmv',x_watson_learning_opt_out=True)
	
	with open(join(dirname(__file__), 'answer.wav'), 'wb') as audio_file:
    		audio_file.write(text_to_speech.synthesize(answer, accept='audio/wav', voice="en-US_AllisonVoice"))

	play_audio()

    



def callback(data):
	
	
	context = {}

	#workspace_id = 'b862e7b6-82f8-4e50-9ebd-e3be4c07d9a9'
	workspace_id = 'f8c86853-434f-4588-baed-226a26f855c0'
	response = conversation.message(workspace_id=workspace_id,message_input={'text': data.data},context=context)
	#json.dumps(response, indent=2)

	
	
	if(len(response[u'output'][u'text']) == 0):
		answer = "Pardon. Can you repeat"
		text_to_speech(answer)
		
	else:
		answer = response[u'output'][u'text'][0]
		text_to_speech(answer)
		
	 
	print answer



def listener():
  
	rospy.init_node('listener', anonymous=True)

	rospy.Subscriber("watson_stt/heard", String, callback)

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
	listener()
