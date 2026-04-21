**Now another funcitonality for debugging. You will use cassandra db. Create the db with the following config and following Schema:**

## CONFIG
- Replication factor: 2
- Voting: Majority
- one master
- two datanodes 


## SCHEMA:
### Single table with the following columns:
- id (optional)
- source
- destination
- action 
- timestamp

# NEW Functionality

## Write log
Whenever any type of call happens either from *api gateway* to *microservice* or vice-versa, it should be written to cassandra db. 

## Get logs
expose *GET* **/logs** endpoint, which returns all logs in .json format from the database. 


# Suggested implementation:
To avoid huge repetetive writes, create a decorator and use it in all relevant functions in api gateway 