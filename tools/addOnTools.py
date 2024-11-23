# # NOTE : Ensure that the output of toolGen.py follows this format


# def Tool1():
#     pass

# def Tool2():
#     pass
# def Tool3():
#     pass

# tool1 = Tool(
#     name='Tool Generator 1',
#     func=Tool1,
#     description="This is to be used to generate new tools"
# )

# tool2 = Tool(
#     name='Tool Generator 1',
#     func=Tool2,
#     description="This is to be used to generate new tools"
# )

# tool3 = Tool(
#     name='Tool Generator 1',
#     func=Tool3,
#     description="This is to be used to generate new tools"
# )


# updated_Tools = [tool1,tool2,tool3]

from langchain.agents import Tool

updatedTools = []