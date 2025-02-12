SYSTEM_EXPLANATION_FOR_PORTFOLIO_ANALYSIS = """You are a portfolio manager. You will receive information about 
                        the portfolio with the stocks and their allocation in it. You need 
                        to suggest changes to the portfolio based on well established financial
                        principles. You need to explain it understandaly for a person without
                        any financial background. Please provide exactly 5 suggestions. Return only a valid JSON in the following format:
                        {{
                            "suggestions": [
                                {{
                                    "title": "Brief title",
                                    "details": "Detailed explanation"
                                }}
                            ]
                        }}"""
                        
SYSTEM_EXPLANATION_FOR_TRADE_ANALYSIS = """You are a portfolio manager. You will receive information about 
                        a trade and all the information about it. You have to analise the trade and provide
                        an explanation for it. You also need to provide some suggestion for the trade. You need to explain it understandaly for a person without
                        any financial background. Return only a valid JSON in the following format:
                        {{
                            "explanation": "Detailed explanation",
                            "suggestion": "Detailed suggestion"
                        }}"""

SUGGESTIONS_EXPLANATIONS = [
    {
        "text": "Based on financial principles, you should diversify your portfolio. You should think about the allocation that you have in: ",
        "indicator": "allocation",
        "to_use_less_comparator": False,
        "value": 20,
    },
    {
        "text": "It is normal for a stock to have a P/E ratio of 15-20. If a stock has a P/E ratio of 20 or more, it is overvalued and you should consider selling it. In your portfolio, the following stocks doesn't follow this principle: ",
        "indicator": "pe_ratio",
        "to_use_less_comparator": False,
        "value": 20,
    },
    {
        "text": "If a stock has an RSI of 70 or more, it is overvalued and you should consider selling it. In your portfolio, the following stocks doesn't follow this principle: ",
        "indicator": "rsi",
        "to_use_less_comparator": False,
        "value": 70,
    },
    {
        "text": "If a stock has an RSI of 30 or less, it is undervalued and you should consider buying it. In your portfolio, the following stocks are considered undervalued: ",
        "indicator": "rsi",
        "to_use_less_comparator": True,
        "value": 30,
    },
]
