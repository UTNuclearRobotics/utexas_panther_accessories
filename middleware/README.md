## Middleware Setup Guide

To set up the middleware, follow the instructions provided in the [Husarnet Cyclone DDS tutorial](https://husarion.com/tutorials/other-tutorials/husarnet-cyclone-dds/#cyclone-dds).

### Important Note
Ensure you follow the steps to add the necessary changes to your `.bashrc` file.

```sh
echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
echo "export CYCLONEDDS_URI=file:///home/$USER/utexas_panther_ws/src/utexas_panther_accessories/middleware/cyclonedds_p2p.xml" >> ~/.bashrc
```

### Chrony
After installing chrony

```sudo apt install chrony```

Put the chrony_client.conf in /etc/chrony/ on the Nuvo as chrony.conf.
Put the chrony_server.conf in /etc/chrony/ on the husarion Pi as chrony.conf.

Restart chrony

```sudo systemctl restart chrony```

Check chrony

```chronyc tracking```