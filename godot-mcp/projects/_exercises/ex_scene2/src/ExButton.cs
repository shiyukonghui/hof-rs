using Godot;

public partial class ExButton : Button
{
    public override void _Ready() { Pressed += OnPressed; }

    private void OnPressed()
    {
        var bg = GetNodeOrNull<ColorRect>("../Background");
        if (bg != null) { bg.Color = new Color(1.0f, 0.0f, 0.0f, 1.0f); }
    }
}
