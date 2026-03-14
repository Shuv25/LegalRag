"""
Test queries for RAGAs evaluation of the Legal RAG pipeline.
Covers LOOKUP and ANALYTICAL query types across Microsoft SEC filing.

To add new company queries:
1. Ingest the PDF via /ingestion endpoint with a new matter name
2. Add new queries following the same dict structure below:
   {
       "question": "your question",
       "matter": "your_matter_name",
       "query_type": "LOOKUP or ANALYTICAL or COMPARATIVE",
       "ground_truth": "expected answer"
   }
3. Add them to TEST_QUERIES list
"""

TEST_QUERIES = [
    # LOOKUP queries
    {
        "question": "What is Microsoft's total revenue for fiscal year 2023?",
        "matter": "microsoft_2024",
        "query_type": "LOOKUP",
        "ground_truth": "Microsoft's total revenue for fiscal year 2023 was $211.9 billion"
    },
    {
        "question": "Who is Microsoft's CEO?",
        "matter": "microsoft_2024",
        "query_type": "LOOKUP",
        "ground_truth": "Microsoft's CEO is Satya Nadella"
    },
    {
        "question": "Where is Microsoft headquartered?",
        "matter": "microsoft_2024",
        "query_type": "LOOKUP",
        "ground_truth": "Microsoft is headquartered in Redmond, Washington"
    },
    {
        "question": "What is Microsoft's net income for 2023?",
        "matter": "microsoft_2024",
        "query_type": "LOOKUP",
        "ground_truth": "Microsoft's net income for fiscal year 2023 was $72.4 billion"
    },
    {
        "question": "What are Microsoft's main product segments?",
        "matter": "microsoft_2024",
        "query_type": "LOOKUP",
        "ground_truth": "Microsoft's main segments are Productivity and Business Processes, Intelligent Cloud and More Personal Computing"
    },

    # ANALYTICAL queries
    {
        "question": "How does Microsoft generate its revenue?",
        "matter": "microsoft_2024",
        "query_type": "ANALYTICAL",
        "ground_truth": "Microsoft generates revenue through cloud services Azure, productivity software Office 365, gaming Xbox and LinkedIn"
    },
    {
        "question": "What are Microsoft's key risk factors?",
        "matter": "microsoft_2024",
        "query_type": "ANALYTICAL",
        "ground_truth": "Microsoft faces risks including cybersecurity threats, competition in cloud services, regulatory scrutiny and dependence on cloud growth"
    },
    {
        "question": "What is Microsoft's cloud strategy?",
        "matter": "microsoft_2024",
        "query_type": "ANALYTICAL",
        "ground_truth": "Microsoft's cloud strategy centers on Azure growth, AI integration across products and expanding enterprise cloud adoption"
    },
    {
        "question": "How does Microsoft invest in research and development?",
        "matter": "microsoft_2024",
        "query_type": "ANALYTICAL",
        "ground_truth": "Microsoft invested approximately $27.2 billion in R&D in 2023 focusing on cloud AI and gaming"
    },
    {
        "question": "What is Microsoft's strategy for AI integration?",
        "matter": "microsoft_2024",
        "query_type": "ANALYTICAL",
        "ground_truth": "Microsoft integrates AI across products through Copilot features in Office, Azure AI services and GitHub Copilot for developers"
    },
]