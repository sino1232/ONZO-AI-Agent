import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

class APIBase:
    def __init__(self, llm_api_key):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm = ChatGroq(
            temperature=0,
            # model="llama3-8b-8192",
            model="llama-3.1-70b-versatile",
            api_key=llm_api_key,
        )
        self.system_context = "Answer the question from given contexts. Always summarize the context in Korean, even if the context is in English."
        self.human_with_context = """
        Context: {context}

        ---

        Question: {question}
        """
        self.prompt_with_context = ChatPromptTemplate.from_messages([("system", self.system_context), ("human", self.human_with_context)])
        self.chain_with_context = self.prompt_with_context | self.llm | StrOutputParser()
