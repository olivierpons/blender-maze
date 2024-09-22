# Blender Maze Generator

A Blender plugin for generating complex and customizable 3D mazes.

[Version française](README_fr.md)

## Features

- Generates 3D mazes with customizable dimensions
- Seamlessly integrates into the Blender interface
- Creates optimized and ready-to-use maze structures
- Offers customization options for wall thickness and spacing

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-name/blender-maze.git
   ```

2. Copy the `python_maze_blender_addon.py` file to your Blender addons folder:
   - Windows: `%APPDATA%\\Blender Foundation\\Blender\\<version>\\scripts\\addons`
   - macOS: `/Users/<user>/Library/Application Support/Blender/<version>/scripts/addons`
   - Linux: `~/.config/blender/<version>/scripts/addons`

3. Activate the addon in Blender:
   - Go to Edit > Preferences > Add-ons
   - Search for "Maze Generator"
   - Check the box to enable the addon

## Usage

1. In Blender, go to "Add > Mesh > Maze v0.1"
2. A 3D maze will be generated with default dimensions (18x15x4)
3. Modify the maze properties in the object properties panel if needed

## Configuration

The project uses Poetry for dependency management. To install dependencies:

```
poetry install
```

## Development

To contribute to the project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Olivier Pons - olivier.pons@gmail.com

Project Link: [https://github.com/your-name/blender-maze](https://github.com/your-name/blender-maze)
