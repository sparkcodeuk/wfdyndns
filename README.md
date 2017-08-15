# wfdyndns - WebFaction Dynamic DNS Updater

A quick python 3 script for WebFaction customers that will help maintain a Dynamic DNS record in their account. Useful for customers who wish to access their office or home network when they don't have a static IP address.

Login to your webfaction account and an empty DNS record you wish to keep updated under "Domains / Websites" => "Domains".

Configure the API username/password details using the same details you use to login to the web control panel, and the DNS record that you want to use as your dynamic DNS record.

Run the script and check that it notifies a DNS update occured, then refresh the domain list in the webfaction control panel and check that the DNS record is now set to the external IP address of the connection you're running the script from.

Depending on various factors the DNS record itself may take some minutes to propagate, especially if you're using an existing record you've already hit.

The script will loop and regularly, checking for updates should your IP address change.
