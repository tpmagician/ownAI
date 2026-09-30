from typing import List
import json
import random
import string
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()


@tool
def write_json(filepath: str, data: dict) -> str:
    '''write a python dictionary as JSON into a text file with nice formatting'''
    try:
        with open(filepath,'w', encoding = 'utf-8') as f:
            json.dump(data, f, indent = 2, ensure_ascii=False)
        return f"Succesfully wrote JSON data to '{filepath}' ({len(json.dumps(data))} characters)."
    except Exception as e:
        return f"Error writing JSON:{str(e)}"



@tool
def read_json(filepath: str) -> str:
    '''read and return the contents of a JSON file'''
    try:
        with open(filepath, 'r',encoding = 'utf-8') as f:
            data = json.load(f)
        return json.dumps(data,indent = 2)
    except FileNotFoundError:
            return f"Error: File '{filepath}' could not be found"
    except json.JSONDecodeError as e:
         return f"Error: Invalid JSON {str(e)}"
    except Exception as e:
         return f"Error reading JSON: {str(e)}"
@tool
def generate_sample_users(
     first_names:List[str],
     last_names:List[str],
     domains:List[str],
     min_age: int,
     max_age: int) -> dict:
     '''generates a list of sample users based on the input of the user '''
     if not first_names:
          return{"error" : "first names list cannot be empty"}
     if not last_names:
          return {"error" : "last names list cannot be empty"}
     if not domains:
          return{"error " :"cannot have empty domains list"}
     if  min_age > max_age:
          return{"error" : "cannot have minumum age be greater than maximum age "}
     if max_age < 0 or min_age < 0:
          return{"error" : "cannot have minimum age or maximum age be less than 0"}
     users = []
     count = len(first_names)

     for i in range(count):
          first = first_names[i]
          last = last_names[i%len(last_names)]
          domain = domains[i%len(domains)]
          email = f"{first.lower()}.{last.lower()}@{domain}"
          user = {
            "id": i+1,
            "firstName" : first,
            "lastName" : last,
            "email" : email,
            "username": f"{first.lower()}{random.randint(100,999)}",
            "age" : random.randint(min_age,max_age),
            "registeredAt" :(datetime.now()-timedelta(days = random.randint(1,365))).isoformat()
               
          }
          users.append(user)
     return {"users" : users, "count" : len(users)}

TOOLS = [write_json,read_json,generate_sample_users]
llm = ChatOpenAI(model = "gpt-4o-mini", temperature = 0)
SYSTEM_PROMPT = "You are DataGen, a helpful assistant that generates sample data for applications. "
"To generate users, you need: first_names (list), last_names (list), domains (list), min_age, max_age. "
"When asked to save users, first generate them with the tool, then immediately use write_json with the result. "
"If the user refers to 'those users' from a previous request, ask them to specify the details again."
agent = create_agent(llm,TOOLS,system_prompt = SYSTEM_PROMPT)


def run_agent(user_input:str, history: List[BaseMessage]) -> AIMessage:
     '''runs the ai agent based on the user input and gives a AI message as a response'''
     try:
          result = agent.invoke({"messages" : history + [HumanMessage(content = user_input)]}, # type: ignore
                                config={"recursion_limit" : 50})
          return result["messages"][-1]
     except Exception as e:
          return AIMessage(content = f"Error:{str(e)}\n\n Please try rephrasing your request or provide more specific details")


if __name__ == '__main__':
     print("=" *60)
     print("DataGenAgent - Sample Data Generator")
     print("=" * 60)
     print("Generate sample user data amd save to JSON files.")
     print()
     print("Examples: ")
     print("- Generate users named John, Jane, and Mike and save it to users.JSON")
     print()
     print("Commands: 'quit' or 'exit' to end" )
     print("=" *60)

     history:List[BaseMessage] = []

     while True:
          user_input = input("You: ").strip()
          # check for exit commands
          if user_input.lower() in ['quit','exit','q',""]:
               print("Goodbye")
               break
          print("Agent: ", end = "", flush = True)
          response = run_agent(user_input,history)
          print(response.content)
          print()
          #update conversation history

          history += [HumanMessage(content = user_input), response]