import requests
import flask


def main(event, context):
    print("hello creature ...")
    print(event)
    print(context)

    return "SUCCESS!"
