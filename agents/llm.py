import os
from huggingface_hub import InferenceClient

client = InferenceClient(
    provider="featherless-ai",
    api_key=os.environ["HUGGING_FACE_API"],
)

# The following test is commented out so it doesn't run during import
# result = client.text_generation(
#     "Can you please let us know more details about your ",
#     model="meta-llama/Llama-3.1-8B",
# )