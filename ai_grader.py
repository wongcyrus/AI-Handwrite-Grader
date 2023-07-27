from langchain.llms import VertexAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate

from langchain.output_parsers import StructuredOutputParser, ResponseSchema


def get_score_and_feedback(prompt, answer):
    parameters = {
        "temperature": 0.9,
        "max_output_tokens": 1000,
        "top_p": 0.95,
        "top_k": 5,
    }
    llm = VertexAI(**parameters)
    prompt_template = PromptTemplate(input_variables=["answer"], template=prompt)
    grader_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="grade_results")
    llm = VertexAI(**parameters)
    final_marks_output_parser = StructuredOutputParser.from_response_schemas(
        [
            ResponseSchema(
                name="final_marks",
                description="'Final Mark' is a number and no explaination.",
                type="int",
            )
        ]
    )
    format_instructions = final_marks_output_parser.get_format_instructions()
    # format_instructions
    grade_results_template = """
    ++++++++++++++++++++
    {grade_results}
    ++++++++++++++++++++

    {format_instructions}
    """
    prompt_template = PromptTemplate(
        input_variables=["grade_results"],
        partial_variables={"format_instructions": format_instructions},
        #  output_parser=final_marks_output_parser, # It will not execute!
        template=grade_results_template,
    )
    final_marks_chain = LLMChain(
        llm=llm, prompt=prompt_template, output_key="final_marks"
    )
    llm = VertexAI(**parameters)
    template = """
    {grade_results}

    Extracts feedbacks
    """
    prompt_template = PromptTemplate(
        input_variables=["grade_results"], template=template
    )
    feedback_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="feedback")

    overall_chain = SequentialChain(
        chains=[grader_chain, final_marks_chain, feedback_chain],
        input_variables=["answer"],
        # Here we return multiple variables
        output_variables=["final_marks", "feedback"],
    )
    retry = 0
    while True:
        try:
            result = overall_chain({"answer": answer})
            marks = final_marks_output_parser.parse(result["final_marks"])[
                "final_marks"
            ]
            feedback = result["feedback"]
            break
        except Exception as ex:
            if retry < 2:
                print("retry: " + str(retry))
                retry += 1
                print(ex)
                continue
            return {
                "answer": answer,
                "marks": 0,
                "feedback": "",
                "error": True,
            }
    return {
        "answer": answer,
        "marks": marks,
        "feedback": feedback,
        "error": False,
    }


if __name__ == "__main__":
    t = """
Question: What is the capital of France?

Answer: {answer}

Final Marks calculation:
1. On a scale of 1 to 10, how closely does your answer resemble the correct one?

Feedbacks:
1. Reasoning the final marks.

Response:
1. Final Marks
2. Feedbacks
    """
    r = get_score_and_feedback(t, "Lyons")
    print(r)
