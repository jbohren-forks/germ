#include <ros/ros.h>
#include <germ_msgs/PredicateInstance.h>
#include <germ_msgs/Predicate.h>
#include <germ_msgs/Object.h>
#include <germ_msgs/PredicateInstanceList.h>

namespace germ_ros {
  void ROS_printPredicate(const germ_msgs::PredicateInstance &pi);

  germ_msgs::PredicateInstance createPredicateInstance(const std::string &predicate_name,
                                            const std::string &parent_name,
                                            const std::string &child_name,
                                            const bool add);
}
