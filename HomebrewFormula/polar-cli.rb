class PolarCli < Formula
  include Language::Python::Virtualenv

  desc "CLI for Polar — manage products, customers, and webhooks from the terminal"
  homepage "https://github.com/berkantay/polar-cli"
  url "https://files.pythonhosted.org/packages/16/05/61de49047d5fbe46e665e22dc1e8be6b31e6e1f2d68c753a1a56cf4125e3/polar_cli-0.1.0.tar.gz"
  sha256 "ad54968d94a0cc47e3be22f4d99119d78ee0baf2b0f27f43d3c3127fa4ab45b4"
  license "Apache-2.0"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "polar", shell_output("#{bin}/polar --help")
  end
end
