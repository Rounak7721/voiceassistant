from groq import Groq
from PIL import ImageGrab, Image
import cv2
import pyperclip
import google.generativeai as genai
import pyaudio

# Initialize the Groq client
groq_client = Groq(api_key="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")
genai.configure(api_key="AIzaSyCvssZnNGZpdjAGnn8U-cTGDMbHHsSaRRQ")
web_cam = cv2.VideoCapture(0)



sys_msg = (
    'You are a multi-model AI Voice Assistant named "SYRA" and gender "Female". Your User may not have attached a photo for context '
    '(either a screenshot or a webcamcapture). Any photo has already been processed into higly detailed '
    'text prompt that will be attached to their transcribed voice prompt. Generate the most useful and '
    'factual response possible, carefully considering all previous generated text in your response before '
    'adding new tokens to the responses. Do not expect or request images, just use the context if added. '
    'Use all of the context of this conversation so your response is relevant to the conversation. Make '
    'your responses clear and concise, avoiding any verbosity.'
)

convo = [{'role':'system', 'content': sys_msg}]



generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}

safety_settings = [
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'BlOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'BlOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'BlOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'BlOCK_NONE'
    },
]

model = genai.GenerativeModel('gemini-1.5-flash-latest',
                              generation_config=generation_config,
                              safety_settings=safety_settings)
# Function to chat with the model and get a response
def groq_prompt(prompt, img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\n\n IMAGE CONTEXT: {img_context}'
    convo.append({'role':'user', 'content': prompt})
    chat_completion = groq_client.chat.completions.create(messages=convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message
    print(response)
    convo.append(response)
    return response.content

# Function to determine the appropriate action based on user input
def function_call(prompt):
    sys_msg = (
        'You are an function AI model that '
        'Determine whether to extract the user clipboard content, take a screenshot, '
        'capture the webcam, or call no functions based on the user prompt. '
        'The webcam can be assumed to be a normal laptop webcam facing the user. '
        'Respond with only one selection from this list: '
        '["extract clipboard", "take screenshot", "capture webcam", "None"]. '
        'Do not provide any explanations; format the response exactly as listed.'
    )

    function_convo = [{'role':'system', 'content': sys_msg},
                      {'role':'user', 'content': prompt}]    
    
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message

    return response.content

def take_screenshot():
    path = 'screenshot.jpg'
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path, quality=15)

def web_cam_capture():
    if not web_cam.isOpened():
        print("Error: Camera did not open.")
        exit()
    else:
        path = 'webcam.jpg'
        ret, frame = web_cam.read()
        cv2.imwrite(path, frame)

def get_clipboard_text():
    clipboard_content = pyperclip.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print("No clipboard text to copy")
        return None

def vision_prompt(prompt, photo_path):
    img = Image.open(photo_path)
    
    # Ensure prompt is a string
    if not isinstance(prompt, str):
        raise TypeError(f"Expected a string for prompt, got {type(prompt)}")
    
    # Prepare the prompt correctly
    vision_prompt_text = (
        'You are the vision analysis AI that provides semantic meaning from images to provide context '
        'to send to another AI that will create a response to the user. Do not respond as the AI assistant '
        'to the user. Instead, take the user prompt input and try to extract all meaning from the photo '
        'relevant to the user prompt. Then generate as much objective data about the image for the AI '
        f'assistant who will respond to the user.\nUSER PROMPT: {prompt}'
    )

    response = model.generate_content([vision_prompt_text, img])
    return response

def speak(text):
    player_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
    stream_start = False

    



# Main loop to interact with the user
while True:
    prompt = input("User: ")
    call = function_call(prompt)

    if 'take screenshot' in call:
        print("Taking Screenshot")
        take_screenshot()
        visual_context = vision_prompt(prompt=prompt, photo_path='screenshot.jpg')
    
    elif 'capture webcam' in call:
        print("Capturing WebCam")
        web_cam_capture()
        visual_context = vision_prompt(prompt=prompt, photo_path='webcam.jpg')
    
    elif 'extract clipboard' in call:
        print("Copying Clipboard text")
        paste = get_clipboard_text()
        prompt = f'{prompt}\n\n CLIPBOARD CONTENT: {paste}'
        visual_context = None
    else:
        visual_context = None
    response = groq_prompt(prompt=prompt, img_context=visual_context)
    print(response)