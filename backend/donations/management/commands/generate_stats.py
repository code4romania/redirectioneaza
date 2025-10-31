from datetime import datetime

from django.core.management import BaseCommand

from donations.models.stat_configs import StatsChoices, create_stat


class Command(BaseCommand):
    help = "Generate the statistics for the dashboard."

    def add_arguments(self, parser):
        parser.add_argument(
            "statistic",
            type=str,
            help="What type of statistic to generate",
            choices=StatsChoices.values,
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Date for which to generate the statistic (YYYY-MM-DD). Required for REDIRECTIONS_PER_DAY.",
        )

    def handle(self, *args, **options):
        statistic_type: str = options["statistic"]
        for_date_str: str = options.get("date")

        if statistic_type == StatsChoices.REDIRECTIONS_PER_DAY and not for_date_str:
            self.stderr.write("Error: --date argument is required for REDIRECTIONS_PER_DAY statistic.")
            return

        self.stdout.write(f"Generating statistics for: {statistic_type}")

        if for_date_str:
            for_date = datetime.strptime(for_date_str, "%Y-%m-%d").date()
            create_stat(stat_choice=StatsChoices(statistic_type), for_date=for_date)
        else:
            create_stat(stat_choice=StatsChoices(statistic_type))
