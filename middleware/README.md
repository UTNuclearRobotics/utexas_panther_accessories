## Middleware Setup Guide

To set up the middleware, follow the instructions provided in the [Husarnet Cyclone DDS tutorial](https://husarion.com/tutorials/other-tutorials/husarnet-cyclone-dds/#cyclone-dds).

### Important Note
Ensure you follow the steps to add the necessary changes to your `.bashrc` file.

```sh
echo "export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp" >> ~/.bashrc
echo "export CYCLONEDDS_URI=file:///home/$USER/utexas_panther_ws/src/utexas_panther_accessories/middleware/cyclonedds.xml" >> ~/.bashrc
```