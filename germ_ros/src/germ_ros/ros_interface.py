#!/usr/bin/env python

import rospy
import germ_msgs.msg as gm
import std_msgs.msg as sm

from germ_neo4j import GermDatabaseConnection

def get_properties(props, name=""):
    data = {}
    for i in range(len(props.key)):
        k = props.key[i]
        v = props.value[i]
        t = props.type[i]

        if len(v) == 0:
            continue

        if t == "float":
            data[k] = float(v)
        else:
            if not t == "string" and not t == "tf_frame":
                rospy.logwarn("Unrecognized type: %s"%(t))
            data[k] = v

    if not len(name) == 0:
        data["name"] = name

def yaml_get_properties(obj):
    data = {}

    if "properties" in obj:
        for elem in obj["properties"]:
            print elem
            k = elem["key"]
            v = elem["value"]
            t = elem["type"]

            if t == "float":
                data[k] = float(v)
            else:
                if not t == "string" and not t == "tf_frame":
                    rospy.logwarn("Unrecognized type: %s"%(t))
                data[k] = v

    if "name" in obj:
        data["name"] = obj["name"]

    return data

class GermROSListener:
    
    def __init__(self, db_address="http://localhost:7474/db/data"):
        self.dbc = GermDatabaseConnection(address)
        rospy.Subscriber("add_predicate", gm.PredicateInstance, self.add_predicate_cb)
        rospy.Subscriber("add_class", sm.String, self.add_class_cb)
        rospy.Subscriber("add_object", gm.Object, self.add_obj_cb)
        rospy.Subscriber("update_predicates", gm.PredicateInstanceList, self.update_predicates_cb)


    def load(self):
        # get the set of definitions
        defs = rospy.get_param("definitions")
        print defs
        print type(defs)

        class_defs = []
        entity_defs = []
        predicate_defs = []
        for name, subset in defs.items():
            print "Loading from subset \"%s\""%(name)
            class_defs = class_defs + subset["classes"]
            entity_defs = entity_defs + subset["entities"]
            predicate_defs = predicate_defs + subset["predicates"]

        for obj_class in class_defs:
            self.dbc.addClass(obj_class)

        for obj in entity_defs:
            self.dbc.addObject(obj["name"], obj["class"], yaml_get_properties(obj))

        for pred in predicate_defs:
            if not self.dbc.addPredicateInstance(pred["parent"], pred["child"], pred["name"], yaml_get_properties(pred)):
                rospy.logerr("Failed to add predicate!")
                rospy.logerr("Predicate = " + pred)

    '''
    add_obj_cb()
    Adds an object with a class.
    '''
    def add_obj_cb(self, msg):
        data = get_properties(msg.data, msg.name)
        self.dbc.addObject(msg.name, msg.obj_class, data)

    '''
    add_class_cb()
    Callback to add a single class to the database, as a string,
    '''
    def add_class_cb(self, msg):
        self.dbc.addClass(msg.data)

    '''
    add_predicate_cb()
    Class to force addition of a single instantiated predicate.
    This ignores the OPERATION field for now.
    '''
    def add_predicate_cb(self, msg):
        data = get_properties(msg.data, msg.predicate.name)
        if not self.dbc.addPredicateInstance(msg.parent.name, msg.child.name, msg.predicate.name, data):
            rospy.logerr("Was not able to add predicate \"%s\" from \"%s\" to \"%s\"; it references unknown entities/classes!"%(msg.predicate.name,msg.parent.name,msg.child.name))

    '''
    update_predicates_cb()
    Takes a whole list of predicates and saves them in the graph database.
    Uses the operation field to determine whether to add or delete.
    '''
    def update_predicates_cb(self, msg):
        for pred in msg.predicates:
            if pred.operation == gm.PredicateInstance.ADD:
                data = get_properties(pred.data, pred.predicate.name)
                if not self.dbc.addPredicateInstance(pred.parent.name, pred.child.name, pred.predicate.name, data):
                    rospy.logerr("Was not able to add predicate \"%s\" from \"%s\" to \"%s\"; it references unknown entities/classes!"%(pred.predicate.name,pred.parent.name,pred.child.name))
            elif pred.operation == gm.PredicateInstance.REMOVE:
                # find and remove this predicate; it's no longer valid
                if not self.dbc.deletePredicateInstance(pred.parent.name, pred.child.name, pred.predicate.name):
                    rospy.logerr("Predicate \"%s\" from \"%s\" to \"%s\" references unknown entities/classes and cannot be removed!"%(pred.predicate.name,pred.parent.name,pred.child.name))
            else:
                rospy.logerr("Unrecognized operation code: \"%d\". Did you forget to set ADD or REMOVE?"%(pred.operation))



if __name__ == "__main__":
    rospy.init_node("germ_ros_interface")

    address = rospy.get_param("~db_address","http://localhost:7474/db/data")
    purge = rospy.get_param("~purge",False)

    rate = rospy.Rate(30)

    try:

        gi = GermROSListener(address)

        if purge == True or purge == "true":
            rospy.logwarn("Deleting current database! Hope you backed up anything important!")
            gi.dbc.purge()
        elif not purge == False and not purge == "false":
            ROSInterruptExceptiony.logwarn('''Unknown value for argument "purge":''' + str(purge))

        gi.load()

        while not rospy.is_shutdown():
            rate.sleep()

    except rospy.ROSInterruptException:
        pass

