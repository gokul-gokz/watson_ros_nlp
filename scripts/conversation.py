import json
import rospy
from std_msgs.msg import String

from watson_developer_cloud import ConversationV1
answer = "a"

conversation = ConversationV1(
  username='24c24760-7d8c-4862-afab-955a5ca63511',
  password='2WvceTeJKH3g',
  version='2017-05-26'
)


def callback(data):
	pub = rospy.Publisher('Robot_response', String, queue_size=10)

	#rospy.loginfo(rospy.get_caller_id() + "I heard %s", data.data)
	context = {}

	#workspace_id = 'b862e7b6-82f8-4e50-9ebd-e3be4c07d9a9'
	workspace_id = 'f8c86853-434f-4588-baed-226a26f855c0'
	response = conversation.message(workspace_id=workspace_id,message_input={'text': data.data},context=context)
	#print(json.dumps(response, indent=2))
        answer = response[u'output'][u'text'][0]
	
	pub.publish(String(answer))
 
	print answer
 
def listener():
  
	rospy.init_node('listener', anonymous=True)

	rospy.Subscriber("watson_stt/heard", String, callback)

	rospy.spin()

if __name__ == '__main__':
	listener()



# Replace with the context obtained from the initial request

