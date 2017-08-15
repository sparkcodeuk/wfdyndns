# wfdyndns - WebFaction Dynamic DNS Updater

A quick python 3 script for WebFaction customers that will help maintain a Dynamic DNS record in their account. Useful for customers who wish to access their office or home network when they don't have a static IP address.

Login to your webfaction account, add an empty DNS record that you wish to keep updated under "Domains / Websites" => "Domains".

Configure the API username/password details using the same credentials you use to login to the web control panel. Configure the DNS record you want to use as your dynamic DNS record.

Run the script and check that it notifies as having updated the DNS record. Refresh the domain list in the webfaction control panel and check that the DNS record is now set to the external IP address of the connection you're running the script from.

Depending on various factors the DNS record itself may take some minutes to fully propagate, especially if you're using an existing record you've already hit recently.

The script will continue to check for updates should your IP address change at any time.
