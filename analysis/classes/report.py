import weasyprint
import os
import json
import hashlib
import re
import sys

from weasyprint import HTML
from pathlib import Path
from datetime import datetime
from utils import get_config


class Report(object):

    def __init__(self, capture_directory):
        self.capture_directory = capture_directory
        self.alerts = self.read_json(os.path.join(
            capture_directory, "assets/alerts.json"))
        self.whitelist = self.read_json(os.path.join(
            capture_directory, "assets/whitelist.json"))
        self.conns = self.read_json(os.path.join(
            capture_directory, "assets/conns.json"))
        self.device = self.read_json(os.path.join(
            capture_directory, "assets/device.json"))
        self.capinfos = self.read_json(os.path.join(
            capture_directory, "assets/capinfos.json"))
        try:
            with open(os.path.join(self.capture_directory, "capture.pcap"), "rb") as f:
                self.capture_sha1 = hashlib.sha1(f.read()).hexdigest()
        except:
            self.capture_sha1 = "N/A"

        self.userlang = get_config(("frontend", "user_lang"))

        # Load template language
        if not re.match("^[a-z]{2,3}$", self.userlang):
            self.userlang = "en"
        with open(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "locales/{}.json".format(self.userlang))) as f:
            self.template = json.load(f)["report"]

    def read_json(self, json_path):
        """
            Read and convert a JSON file.
            :return: array or dict.
        """
        with open(json_path, "r") as json_file:
            return json.load(json_file)

    def generate_report(self):
        """
            Generate the full report in PDF
            :return: nothing
        """
        content = self.generate_page_header()
        content += self.generate_header()
        content += self.generate_warning()
        content += self.generate_alerts()
        content += self.generate_suspect_conns_block()
        content += self.generate_uncat_conns_block()
        content += self.generate_whitelist_block()

        htmldoc = HTML(string=content, base_url="").write_pdf()
        Path(os.path.join(self.capture_directory,
                          "report.pdf")).write_bytes(htmldoc)

    def generate_warning(self):
        """
            Generate the warning message.
            :return: str
        """
        if len(self.alerts["high"]):
            msg = "<div class=\"warning high\">"
            msg += self.template["high_msg"].format(
                self.nb_translate(len(self.alerts["high"])))
            msg += "</div>"
            return msg
        elif len(self.alerts["moderate"]):
            msg = "<div class=\"warning moderate\">"
            msg += self.template["moderate_msg"].format(
                self.nb_translate(len(self.alerts["moderate"])))
            msg += "</div>"
            return msg
        elif len(self.alerts["low"]):
            msg = "<div class=\"warning low\">"
            msg += self.template["low_msg"].format(
                self.nb_translate(len(self.alerts["low"])))
            msg += "</div>"
            return msg
        else:
            msg = "<div class=\"warning low\">"
            msg += self.template["none_msg"]
            msg += "</div>"
            return msg

    def nb_translate(self, nb):
        """
            Translate a number in a string.
            :return: str
        """
        a = self.template["numbers"]
        return a[nb-1] if nb <= 9 else str(nb)

    def generate_suspect_conns_block(self):
        """
            Generate the table of the network non-whitelisted communications.
            :return: string
        """

        if not len([c for c in self.conns if c["alert_tiggered"] == True]):
            return ""

        title = "<h2>{}</h2>".format(self.template["suspect_title"])
        table = "<table>"
        table += "    <thead>"
        table += "        <tr>"
        table += "             <th>{}</th>".format(self.template["protocol"])
        table += "             <th>{}</th>".format(self.template["domain"])
        table += "             <th>{}</th>".format(self.template["dst_ip"])
        table += "             <th>{}</th>".format(self.template["dst_port"])
        table += "        </tr>"
        table += "    </thead>"
        table += "<tbody>"

        for rec in self.conns:
            if rec["alert_tiggered"] == True:
                table += "<tr>"
                table += "<td>{}</td>".format(rec["proto"].upper())
                table += "<td>{}</td>".format(rec["resolution"]
                                              if rec["resolution"] != rec["ip_dst"] else "--")
                table += "<td>{}</td>".format(rec["ip_dst"])
                table += "<td>{}</td>".format(rec["port_dst"])
                table += "</tr>"
        table += "</tbody></table>"
        return title + table

    def generate_uncat_conns_block(self):
        """
            Generate the table of the network non-whitelisted communications.
            :return: string
        """
        if not len([c for c in self.conns if c["alert_tiggered"] == False]):
            return ""

        title = "<h2>{}</h2>".format(self.template["uncat_title"])
        table = "<table>"
        table += "    <thead>"
        table += "        <tr>"
        table += "             <th>{}</th>".format(self.template["protocol"])
        table += "             <th>{}</th>".format(self.template["domain"])
        table += "             <th>{}</th>".format(self.template["dst_ip"])
        table += "             <th>{}</th>".format(self.template["dst_port"])
        table += "        </tr>"
        table += "    </thead>"
        table += "<tbody>"

        for rec in self.conns:
            if rec["alert_tiggered"] == False:
                table += "<tr>"
                table += "<td>{}</td>".format(rec["proto"].upper())
                table += "<td>{}</td>".format(rec["resolution"]
                                              if rec["resolution"] != rec["ip_dst"] else "--")
                table += "<td>{}</td>".format(rec["ip_dst"])
                table += "<td>{}</td>".format(rec["port_dst"])
                table += "</tr>"
        table += "</tbody></table>"
        return title + table

    def generate_whitelist_block(self):
        """
            Generate the table of the whitelisted communications.
            :return: string
        """
        if not len(self.whitelist):
            return ""

        title = "<h2>{}</h2>".format(self.template["whitelist_title"])
        table = "<table>"
        table += "    <thead>"
        table += "        <tr>"
        table += "             <th>{}</th>".format(self.template["protocol"])
        table += "             <th>{}</th>".format(self.template["domain"])
        table += "             <th>{}</th>".format(self.template["dst_ip"])
        table += "             <th>{}</th>".format(self.template["dst_port"])
        table += "        </tr>"
        table += "    </thead>"
        table += "<tbody>"

        for rec in sorted(self.whitelist, key=lambda k: k['resolution']):
            table += "<tr>"
            table += "<td>{}</td>".format(rec["proto"].upper())
            table += "<td>{}</td>".format(rec["resolution"]
                                          if rec["resolution"] != rec["ip_dst"] else "--")
            table += "<td>{}</td>".format(rec["ip_dst"])
            table += "<td>{}</td>".format(rec["port_dst"])
            table += "</tr>"
        table += "</tbody></table>"
        return title + table

    def generate_header(self):
        """
            Generate the report header with context data.
            :return: string
        """
        header = "<div class=\"header\">"
        header += "<div class=\"logo\"></div>"
        header += "<p><br /><strong>{}: {}</strong><br />".format(self.template["device_name"],
                                                                  self.device["name"])
        header += "{}: {}<br />".format(self.template["device_mac"],
                                        self.device["mac_address"])
        header += "{} {}<br />".format(self.template["report_generated_on"],
                                       datetime.now().strftime("%d/%m/%Y - %H:%M:%S"))
        header += "{}: {}s<br />".format(self.template["capture_duration"],
                                         self.capinfos["Capture duration"])
        header += "{}: {}<br />".format(self.template["packets_number"],
                                        self.capinfos["Number of packets"])
        header += "{}: {}<br />".format(
            self.template["capture_sha1"], self.capture_sha1)
        header += "</p>"
        header += "</div>"
        return header

    def generate_alerts(self):
        """
            Generate the alerts.
            :return: string
        """
        alerts = "<ul class=\"alerts\">"
        for alert in self.alerts["high"]:
            alerts += "<li class =\"alert\">"
            alerts += "<span class=\"high-label\">High</span>"
            alerts += "<span class=\"alert-id\">{}</span>".format(alert["id"])
            alerts += "<div class = \"alert-body\">"
            alerts += "<span class=\"title\">{}</span>".format(alert["title"])
            alerts += "<p class=\"description\">{}</p>".format(
                alert["description"])
            alerts += "</div>"
            alerts += "</li>"

        for alert in self.alerts["moderate"]:
            alerts += "<li class =\"alert\">"
            alerts += "<span class=\"moderate-label\">moderate</span>"
            alerts += "<span class=\"alert-id\">{}</span>".format(alert["id"])
            alerts += "<div class = \"alert-body\">"
            alerts += "<span class=\"title\">{}</span>".format(alert["title"])
            alerts += "<p class=\"description\">{}</p>".format(
                alert["description"])
            alerts += "</div>"
            alerts += "</li>"
        for alert in self.alerts["low"]:
            alerts += "<li class =\"alert\">"
            alerts += "<span class=\"low-label\">low</span>"
            alerts += "<span class=\"alert-id\">{}</span>".format(alert["id"])
            alerts += "<div class = \"alert-body\">"
            alerts += "<span class=\"title\">{}</span>".format(alert["title"])
            alerts += "<p class=\"description\">{}</p>".format(
                alert["description"])
            alerts += "</div>"
            alerts += "</li>"

        alerts += "</ul>"
        return alerts

    def generate_page_footer(self):
        """
            Generate the html footer.
            :return: string
        """
        return "</body></html>"

    def generate_page_header(self):
        """
            Generate the html header.
            :return: string
        """
        return """<html
                    <head>
                        <style>
                            * {
                                font-family: Arial, Helvetica, sans-serif;
                            }

                            h2 {
                                padding-top: 30px;
                                font-weight: 400;
                                font-size: 18px;
                            }

                            td {
                                width: auto;
                                padding: 10px;
                            }

                            table {
                                background: #FFF;
                                border: 2px solid #FAFAFA;
                                border-radius: 5px;
                                border-collapse: separate;
                                border-spacing: 0px;
                                width: 100%;
                                font-size: 12px;
                            }

                            p {
                                font-size: 13px;
                            }

                            thead tr th {
                                border-bottom: 1px solid #CCC;
                                border-collapse: separate;
                                border-spacing: 5px 5px;
                                background-color: #FFF;
                                padding: 10px;
                                text-align: left;
                            }

                            tbody tr#first td {
                                border-top: 3px solid #4d4d4d;
                                border-collapse: separate;
                                border-spacing: 5px 5px;
                            }

                            tr:nth-of-type(odd) {
                                background-color: #fafafa;
                            }

                            .logo {
                                background-image: url("data:image/png;base64,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");
                                width: 200px;
                                height: 60px;
                                background-size: cover;
                                position: absolute;
                                right: 0px;
                            }

                            .warning {
                                padding: 10px;
                                text-align: center;
                                border-radius: 5px;
                                color: #FFF;
                                margin-top: 40px;
                                margin-bottom: 40px;
                                font-weight:900;
                            }

                            .high {
                                background-color: #F44336;
                            }

                            .moderate {
                                background-color: #ff7e33eb;
                            }

                            .low {
                                background-color: #4fce0eb8;
                            }

                            ul {
                                list-style: none;
                                margin: 0;
                                padding: 0;
                            }

                            .alert {
                                margin-top: 15px;
                            }

                            .alert-body {
                                background-color: #FFF;
                                list-style: none;
                                padding: 10px;
                                border-radius: 5px;
                                border: 1px solid #EEE;
                                margin-top: 3px;
                            }

                            .alert-body>.title {
                                display: block;
                                padding: 5px 5px 5px 10px;
                                font-size: 13px;
                            }

                            .high-label {
                                background-color: #F44336;
                                padding: 5px;
                                text-transform: uppercase;
                                font-size: 10px;
                                font-weight: bold;
                                border-radius: 3px 0px 0px 0px;
                                margin: 0px;
                                color: #FFF;
                                margin-left: 10px;
                            }

                            .moderate-label {
                                background-color: #ff7e33eb;
                                padding: 5px;
                                text-transform: uppercase;
                                font-size: 10px;
                                font-weight: bold;
                                border-radius: 3px 0px 0px 0px;
                                margin: 0px;
                                color: #FFF;
                                margin-left: 10px;
                            }

                            .low-label {
                                background-color: #4fce0eb8;
                                padding: 5px;
                                text-transform: uppercase;
                                font-size: 10px;
                                font-weight: bold;
                                border-radius: 3px 0px 0px 0px;
                                margin: 0px;
                                color: #FFF;
                                margin-left: 10px;
                            }

                            .description {
                                margin: 0;
                                padding: 10px;
                                color:#333;
                                font-size:12px;
                            }

                            ul {
                                list-style: none;
                                margin: 0;
                                padding: 0;
                            }

                            .alert-id {
                                background-color: #636363;
                                padding: 5px;
                                text-transform: uppercase;
                                font-size: 10px;
                                font-weight: bold;
                                border-radius: 0px 3px 0px 0px;
                                margin: 0px;
                                color: #FFF;
                                margin-right: 10px;
                            }
                 
                            .header>p {
                                font-size:12px;
                            }
                            @page {
                                @top-center { 
                                    content: "REPORT_HEADER - Page " counter(page) " / " counter(pages) ".";
                                    font-size:12px;
                                    color:#CCC;
                                }
                                @bottom-center { 
                                    content: "REPORT_FOOTER";
                                    font-size:12px;  
                                    color:#CCC;
                                }
                            }   
                        </style>
                    </head>
                    <body>""".replace("REPORT_HEADER", "{} {}".format(self.template["report_for_the_capture"], self.capture_sha1)).replace("REPORT_FOOTER", self.template["report_footer"])
