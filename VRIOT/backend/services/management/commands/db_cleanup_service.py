import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from common.db_models.device_models import DeviceAuth

mongo_log = settings.MONGO_LOGGER


class Command(BaseCommand):
    help = 'This service is used to cleanup the Database with old deleted ' \
           'data or other clean-ups'

    def __init__(self):
        super(Command, self).__init__()

    def add_arguments(self, parser):
        parser.add_argument('clean_up', nargs='+',
                            help="The type of cleanup to be done. Multiple "
                                 "arguments can be passed. Args accepted: "
                                 "clean_deleted, clean_scan_list")
        # parser.add_argument('--day', type=int,
        #                     help="The type of cleanup to be done. Multiple "
        #                          "arguments can be passed. Args accepted: "
        #                          "clean_deleted, clean_scan_list")
        parser.add_argument('--seconds', type=int,
                            help="The number of seconds of old data to be "
                                 "deleted")

    def handle(self, *args, **options):
        try:
            operations = {
                "clean_deleted": self.clean_deleted,
                "clean_scan_list": self.clean_scan_list
            }
            for operation in options["clean_up"]:
                operations[operation](**options)
        except Exception as e:
            print(e)

    def clean_deleted(self, **options):
        print("Cleaned Deleted")

    @staticmethod
    def clean_scan_list(**options):
        try:
            seconds = options.get("seconds") if options.get("seconds") else 900
            query = {
                "discovered_mode": 0,
                "is_user_allowed": False,
                "created_on": {"$lt": datetime.datetime.now() -
                                      datetime.timedelta(seconds=seconds)}
            }
            records_deleted = DeviceAuth.delete(query=query, hard_delete=True)
            mongo_log.debug("Deleted {} scanned devices which were {} seconds "
                            "and older".format(records_deleted, seconds))
        except Exception as e:
            raise e
