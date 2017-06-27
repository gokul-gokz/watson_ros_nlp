"""Sample code to use the IBM Watson Speech to Text API.
See more at https://blog.rmotr.com.
"""
import json
import rospy
import time

from std_msgs.msg import String
from std_msgs.msg import Float32

from watson_developer_cloud import SpeechToTextV1

class WatsonSTTPub(object):
	def __init__(self):
		self.pub = rospy.Publisher('Speech_Text', String, queue_size=10)
		self.pub1 = rospy.Publisher('Confidence', Float32, queue_size=10)
		self.IBM_USERNAME = "c9201979-fa56-4281-8628-940e6f35fb3a"
		self.IBM_PASSWORD = "DdUs6NEJPpnm"
		self.recognize()

	def recognize(self):
		while(1):
			stt = SpeechToTextV1(username=self.IBM_USERNAME, password=self.IBM_PASSWORD)
			audio_file = open("/home/asimov/watson_ws/src/watson_ros_nlp/scripts/sound_snippets/hai.wav", "rb")
			with open('transcript_result.json', 'w') as fp:
				result = stt.recognize(audio_file, content_type="audio/wav",
                           	  continuous=True, timestamps=False,
                           	  max_alternatives=1)
				for i in range(len(result[u'results'])):
					sentence = result[u'results'][i][u'alternatives'][0][u'transcript']
                                	confidence = result[u'results'][i][u'alternatives'][0][u'confidence']
					print result[u'results'][i][u'alternatives'][0][u'transcript']
					print result[u'results'][i][u'alternatives'][0][u'confidence']
					self.pub.publish(String(sentence))
                                	self.pub1.publish(Float32(confidence))
			time.sleep(10)
			
			json.dump(result, fp, indent=2)
			
    			

if __name__ == '__main__':
    rospy.init_node('watson_stt')
    wsttp = WatsonSTTPub()
    rospy.spin()
