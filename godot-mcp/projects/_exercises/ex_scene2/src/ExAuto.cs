using Godot;

public partial class ExAuto : Node
{
    public int Ticks { get; private set; }
    public override void _Ready() { Ticks = 0; }
}
