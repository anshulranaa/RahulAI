from langchain.agents import Tool


def testTool(input):
    import os

    # Specify the directory you want to list
    directory = "."  # Current directory

    # Specify the output file
    output_file = "output.txt"

    # Get the list of files and directories
    contents = os.listdir(directory)

    # Write the contents to the output file
    with open(output_file, "w") as file:
        for item in contents:
            file.write(item + "\n")

    print(f"Directory listing saved to {output_file}")

test = Tool(
    name='TestingTool',
    func=testTool,
    description="Execute when the user wants to invoke the testing tool"
)
